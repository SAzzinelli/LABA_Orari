#!/usr/bin/env python3
"""
Script per correggere il fuso orario negli orari JSON.

Il problema: tutti gli orari hanno +02:00 quando molti dovrebbero avere +01:00
In Italia:
- Da fine ottobre a fine marzo: CET (UTC+1) = +01:00
- Da fine marzo a fine ottobre: CEST (UTC+2) = +02:00

Le date di cambio ora solare in Italia (ultima domenica del mese):
- Marzo: passa a CEST (+02:00)
- Ottobre: passa a CET (+01:00)
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import re

def get_dst_transition_dates(year: int) -> tuple:
    """
    Calcola le date di cambio ora legale per un anno.
    Ritorna (inizio_cest, fine_cest) dove:
    - inizio_cest: ultima domenica di marzo (inizia CEST)
    - fine_cest: ultima domenica di ottobre (finisce CEST, inizia CET)
    """
    # Ultima domenica di marzo
    # Partiamo dal 31 marzo e andiamo indietro fino a trovare una domenica
    for day in range(31, 24, -1):
        date = datetime(year, 3, day)
        if date.weekday() == 6:  # 6 = domenica
            inizio_cest = date
            break
    
    # Ultima domenica di ottobre
    # Partiamo dal 31 ottobre e andiamo indietro fino a trovare una domenica
    for day in range(31, 24, -1):
        date = datetime(year, 10, day)
        if date.weekday() == 6:  # 6 = domenica
            fine_cest = date
            break
    
    return inizio_cest, fine_cest

def get_correct_timezone(date_str: str) -> str:
    """
    Determina il fuso orario corretto per una data.
    Ritorna "+01:00" (CET) o "+02:00" (CEST)
    """
    try:
        # Rimuovi il timezone esistente per parsare la data
        if '+' in date_str:
            date_without_tz = date_str.split('+')[0]
        elif 'Z' in date_str:
            date_without_tz = date_str.replace('Z', '')
        else:
            date_without_tz = date_str
        
        # Parse la data completa (senza timezone)
        dt = datetime.fromisoformat(date_without_tz)
        
        year = dt.year
        inizio_cest, fine_cest = get_dst_transition_dates(year)
        
        # Se la data è tra inizio_cest e fine_cest -> CEST (+02:00)
        # Altrimenti -> CET (+01:00)
        if inizio_cest <= dt < fine_cest:
            return "+02:00"
        else:
            return "+01:00"
    except Exception as e:
        print(f"⚠️  Errore parsing data {date_str}: {e}")
        return "+02:00"  # Default

def fix_timezone_in_event(event: Dict) -> Dict:
    """Corregge il fuso orario in un evento"""
    fixed = event.copy()
    
    # Corregge start
    if 'start' in fixed and fixed['start']:
        start = fixed['start']
        if '+02:00' in start:
            correct_tz = get_correct_timezone(start)
            fixed['start'] = start.replace('+02:00', correct_tz)
    
    # Corregge end
    if 'end' in fixed and fixed['end']:
        end = fixed['end']
        if '+02:00' in end:
            correct_tz = get_correct_timezone(end)
            fixed['end'] = end.replace('+02:00', correct_tz)
    
    return fixed

def fix_timezone_in_file(input_file: str, output_file: str = None, dry_run: bool = False) -> Dict:
    """
    Corregge il fuso orario in un file JSON.
    Ritorna statistiche delle correzioni.
    """
    if output_file is None:
        output_file = input_file
    
    # Carica il file
    with open(input_file, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    fixed_events = []
    stats = {
        'total': len(events),
        'fixed_start': 0,
        'fixed_end': 0,
        'unchanged': 0
    }
    
    for event in events:
        original_start = event.get('start', '')
        original_end = event.get('end', '')
        
        fixed = fix_timezone_in_event(event)
        fixed_events.append(fixed)
        
        # Conta le correzioni
        if original_start != fixed.get('start', ''):
            stats['fixed_start'] += 1
        if original_end != fixed.get('end', ''):
            stats['fixed_end'] += 1
        if original_start == fixed.get('start', '') and original_end == fixed.get('end', ''):
            stats['unchanged'] += 1
    
    # Salva se non è dry run
    if not dry_run:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_events, f, indent=2, ensure_ascii=False)
    
    return stats

def fix_timezone_in_directory(directory: str, dry_run: bool = False):
    """Corregge il fuso orario in tutti i file JSON di una directory ricorsivamente"""
    dir_path = Path(directory)
    json_files = list(dir_path.rglob('*.json'))
    
    total_stats = {
        'files': 0,
        'total_events': 0,
        'fixed_start': 0,
        'fixed_end': 0,
        'unchanged': 0
    }
    
    for json_file in json_files:
        print(f"\n📄 Processando: {json_file}")
        stats = fix_timezone_in_file(str(json_file), dry_run=dry_run)
        
        total_stats['files'] += 1
        total_stats['total_events'] += stats['total']
        total_stats['fixed_start'] += stats['fixed_start']
        total_stats['fixed_end'] += stats['fixed_end']
        total_stats['unchanged'] += stats['unchanged']
        
        print(f"   Eventi: {stats['total']}")
        print(f"   Start corretti: {stats['fixed_start']}")
        print(f"   End corretti: {stats['fixed_end']}")
        print(f"   Invariati: {stats['unchanged']}")
    
    print(f"\n{'='*60}")
    print(f"📊 Riepilogo totale:")
    print(f"   File processati: {total_stats['files']}")
    print(f"   Eventi totali: {total_stats['total_events']}")
    print(f"   Start corretti: {total_stats['fixed_start']}")
    print(f"   End corretti: {total_stats['fixed_end']}")
    print(f"   Invariati: {total_stats['unchanged']}")
    if dry_run:
        print(f"\n⚠️  DRY RUN - Nessun file è stato modificato")

def main():
    parser = argparse.ArgumentParser(
        description='Corregge il fuso orario negli orari JSON (+02:00 -> +01:00 quando necessario)'
    )
    parser.add_argument('--input', help='File JSON singolo da correggere')
    parser.add_argument('--output', help='File JSON di output (default: sovrascrive input)')
    parser.add_argument('--directory', help='Directory da processare ricorsivamente (tutti i .json)')
    parser.add_argument('--dry-run', action='store_true', help='Mostra cosa verrebbe corretto senza modificare i file')
    
    args = parser.parse_args()
    
    if args.directory:
        print(f"🔍 Processando directory: {args.directory}")
        if args.dry_run:
            print("⚠️  MODALITÀ DRY RUN - Nessun file verrà modificato")
        fix_timezone_in_directory(args.directory, dry_run=args.dry_run)
    elif args.input:
        print(f"📄 Processando file: {args.input}")
        if args.dry_run:
            print("⚠️  MODALITÀ DRY RUN - Nessun file verrà modificato")
        stats = fix_timezone_in_file(args.input, args.output, dry_run=args.dry_run)
        print(f"\n📊 Statistiche:")
        print(f"   Eventi totali: {stats['total']}")
        print(f"   Start corretti: {stats['fixed_start']}")
        print(f"   End corretti: {stats['fixed_end']}")
        print(f"   Invariati: {stats['unchanged']}")
    else:
        parser.print_help()
        print("\n❌ Specificare --input o --directory")

if __name__ == '__main__':
    main()


