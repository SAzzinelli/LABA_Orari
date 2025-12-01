#!/usr/bin/env python3
"""
Script per correggere l'offset di 1 ora negli orari.

Il problema: tutti gli orari hanno 1 ora in più rispetto a quelli reali.
Esempio: 10:30-12:30 dovrebbe essere 9:30-11:30

Questo script sottrae 1 ora da tutti gli orari start e end.
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

def subtract_one_hour(date_str: str) -> str:
    """
    Sottrae 1 ora da una stringa datetime ISO8601.
    Mantiene il fuso orario corretto.
    """
    try:
        # Parse la data con timezone
        if '+' in date_str:
            dt = datetime.fromisoformat(date_str)
        elif 'Z' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str)
        
        # Sottrai 1 ora
        dt_corrected = dt - timedelta(hours=1)
        
        # Ritorna in formato ISO8601 con timezone
        return dt_corrected.isoformat()
    except Exception as e:
        print(f"⚠️  Errore parsing data {date_str}: {e}")
        return date_str

def fix_hour_in_event(event: Dict) -> Dict:
    """Corregge l'offset di 1 ora in un evento"""
    fixed = event.copy()
    
    # Corregge start
    if 'start' in fixed and fixed['start']:
        fixed['start'] = subtract_one_hour(fixed['start'])
    
    # Corregge end
    if 'end' in fixed and fixed['end']:
        fixed['end'] = subtract_one_hour(fixed['end'])
    
    return fixed

def fix_hour_in_file(input_file: str, output_file: str = None, dry_run: bool = False) -> Dict:
    """
    Corregge l'offset di 1 ora in un file JSON.
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
        'fixed': 0
    }
    
    for event in events:
        fixed = fix_hour_in_event(event)
        fixed_events.append(fixed)
        stats['fixed'] += 1
    
    # Salva se non è dry run
    if not dry_run:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_events, f, indent=2, ensure_ascii=False)
    
    return stats

def fix_hour_in_directory(directory: str, dry_run: bool = False):
    """Corregge l'offset di 1 ora in tutti i file JSON di una directory ricorsivamente"""
    dir_path = Path(directory)
    json_files = list(dir_path.rglob('*.json'))
    
    total_stats = {
        'files': 0,
        'total_events': 0,
        'fixed': 0
    }
    
    for json_file in json_files:
        print(f"\n📄 Processando: {json_file}")
        stats = fix_hour_in_file(str(json_file), dry_run=dry_run)
        
        total_stats['files'] += 1
        total_stats['total_events'] += stats['total']
        total_stats['fixed'] += stats['fixed']
        
        print(f"   Eventi corretti: {stats['fixed']}/{stats['total']}")
    
    print(f"\n{'='*60}")
    print(f"📊 Riepilogo totale:")
    print(f"   File processati: {total_stats['files']}")
    print(f"   Eventi totali: {total_stats['total_events']}")
    print(f"   Eventi corretti: {total_stats['fixed']}")
    if dry_run:
        print(f"\n⚠️  DRY RUN - Nessun file è stato modificato")

def main():
    parser = argparse.ArgumentParser(
        description='Corregge l\'offset di 1 ora negli orari JSON (sottrae 1 ora da tutti gli orari)'
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
        fix_hour_in_directory(args.directory, dry_run=args.dry_run)
    elif args.input:
        print(f"📄 Processando file: {args.input}")
        if args.dry_run:
            print("⚠️  MODALITÀ DRY RUN - Nessun file verrà modificato")
        stats = fix_hour_in_file(args.input, args.output, dry_run=args.dry_run)
        print(f"\n📊 Statistiche:")
        print(f"   Eventi totali: {stats['total']}")
        print(f"   Eventi corretti: {stats['fixed']}")
    else:
        parser.print_help()
        print("\n❌ Specificare --input o --directory")

if __name__ == '__main__':
    main()

