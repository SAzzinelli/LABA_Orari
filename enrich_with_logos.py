#!/usr/bin/env python3
"""
Script per arricchire i JSON degli orari con oidCorso da LOGOS

Questo script:
1. Legge i JSON degli orari estratti dai DOCX
2. Fa matching tra nomi corsi e oidCorso da LOGOS
3. Aggiunge oidCorso agli eventi

Uso:
    python enrich_with_logos.py --input "orari/gd-1.json" --output "orari/gd-1-enriched.json" --token "YOUR_LOGOS_TOKEN"
    
Oppure con mappatura locale:
    python enrich_with_logos.py --input "orari/gd-1.json" --output "orari/gd-1-enriched.json" --mapping "logos_course_mapping.json"
"""

import json
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional
import re

def normalize_course_name(name: str) -> str:
    """Normalizza il nome del corso per il matching (come fa l'app Swift)"""
    if not name:
        return ""
    # Rimuovi caratteri speciali, normalizza spazi, lowercase
    normalized = re.sub(r'[^\w\s]', '', name.lower())
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    return normalized

def load_logos_mapping_from_api(token: str) -> Dict[str, str]:
    """
    Carica la mappatura corso -> oidCorso dall'API LOGOS
    Usa l'endpoint Enrollments per ottenere tutti i corsi disponibili
    """
    url = "https://logosuni.laba.biz/logosuni.servicesv2/api/Enrollments"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Errore API LOGOS: {response.status_code}")
            return {}
        
        data = response.json()
        if not data.get('success') or not data.get('payload'):
            print("❌ Risposta API LOGOS non valida")
            return {}
        
        mapping = {}
        esami = data['payload'].get('situazioneEsami', [])
        
        for esame in esami:
            corso_name = esame.get('corso', '')
            oid = esame.get('oidCorso', '')
            if corso_name and oid:
                normalized = normalize_course_name(corso_name)
                # Mantieni il primo oidCorso trovato per ogni corso normalizzato
                if normalized and normalized not in mapping:
                    mapping[normalized] = oid
                    # Aggiungi anche varianti comuni
                    if '1' in corso_name or 'primo' in corso_name.lower():
                        mapping[normalized + ' 1'] = oid
                    if '2' in corso_name or 'secondo' in corso_name.lower():
                        mapping[normalized + ' 2'] = oid
                    if '3' in corso_name or 'terzo' in corso_name.lower():
                        mapping[normalized + ' 3'] = oid
        
        print(f"✅ Caricati {len(mapping)} corsi da LOGOS")
        return mapping
        
    except Exception as e:
        print(f"❌ Errore chiamata API LOGOS: {e}")
        return {}

def load_logos_mapping_from_file(mapping_file: str) -> Dict[str, str]:
    """Carica la mappatura da un file JSON locale"""
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                # Se è una lista di corsi con oidCorso
                mapping = {}
                for item in data:
                    corso = item.get('corso', '')
                    oid = item.get('oidCorso', '')
                    if corso and oid:
                        normalized = normalize_course_name(corso)
                        if normalized:
                            mapping[normalized] = oid
                return mapping
    except Exception as e:
        print(f"❌ Errore caricamento mapping: {e}")
        return {}
    return {}

def enrich_events_with_oid(events: List[Dict], mapping: Dict[str, str]) -> List[Dict]:
    """Aggiunge oidCorso agli eventi basandosi sul nome del corso"""
    enriched = []
    matched = 0
    unmatched = []
    
    for event in events:
        corso = event.get('corso', '')
        if not corso:
            enriched.append(event)
            continue
        
        # Normalizza il nome del corso
        normalized = normalize_course_name(corso)
        
        # Cerca match esatto
        oid = mapping.get(normalized)
        
        # Se non trovato, prova varianti (con/senza anno, numeri, etc.)
        if not oid:
            # Prova senza numeri finali
            base = re.sub(r'\s+\d+$', '', normalized)
            oid = mapping.get(base)
            
            # Prova con anno estratto dal nome
            if not oid:
                year_match = re.search(r'\b([123])\b', corso)
                if year_match:
                    year = year_match.group(1)
                    oid = mapping.get(f"{base} {year}")
        
        if oid:
            event['oidCorso'] = oid
            matched += 1
        else:
            # Mantieni oidCorso null se presente, altrimenti non aggiungere il campo
            if 'oidCorso' not in event:
                event['oidCorso'] = None
            unmatched.append(corso)
        
        enriched.append(event)
    
    # Report
    unique_unmatched = sorted(set(unmatched))
    print(f"\n📊 Matching completato:")
    print(f"   ✅ Matched: {matched}/{len(events)} eventi")
    print(f"   ⚠️  Unmatched: {len(unique_unmatched)} corsi unici")
    if unique_unmatched:
        print(f"\n   Corsi senza match:")
        for corso in unique_unmatched[:10]:  # Mostra primi 10
            print(f"      - {corso}")
        if len(unique_unmatched) > 10:
            print(f"      ... e altri {len(unique_unmatched) - 10}")
    
    return enriched

def main():
    parser = argparse.ArgumentParser(description='Arricchisce JSON orari con oidCorso da LOGOS')
    parser.add_argument('--input', required=True, help='File JSON input')
    parser.add_argument('--output', required=True, help='File JSON output')
    parser.add_argument('--token', help='Token LOGOS (Bearer token)')
    parser.add_argument('--mapping', help='File JSON con mappatura locale corso -> oidCorso')
    parser.add_argument('--save-mapping', help='Salva la mappatura LOGOS in un file JSON')
    
    args = parser.parse_args()
    
    # Carica eventi
    print(f"📂 Caricando: {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except Exception as e:
        print(f"❌ Errore caricamento: {e}")
        return
    
    print(f"   Eventi trovati: {len(events)}")
    
    # Carica mappatura
    mapping = {}
    if args.mapping:
        print(f"\n📋 Caricando mappatura da: {args.mapping}")
        mapping = load_logos_mapping_from_file(args.mapping)
    elif args.token:
        print(f"\n🌐 Caricando mappatura da LOGOS API...")
        mapping = load_logos_mapping_from_api(args.token)
        
        # Salva mapping se richiesto
        if args.save_mapping and mapping:
            with open(args.save_mapping, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
            print(f"   💾 Mappatura salvata in: {args.save_mapping}")
    else:
        print("❌ Fornire --token o --mapping")
        return
    
    if not mapping:
        print("❌ Nessuna mappatura disponibile")
        return
    
    # Arricchisci eventi
    print(f"\n🔄 Arricchendo eventi con oidCorso...")
    enriched = enrich_events_with_oid(events, mapping)
    
    # Salva
    print(f"\n💾 Salvando: {args.output}")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Completato!")

if __name__ == '__main__':
    main()



