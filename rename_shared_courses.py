#!/usr/bin/env python3
"""
Script per rinominare corsi condivisi in modo specifico per ogni corso di studio.

Es: "Informatica di Base" -> "Informatica di Base Design" per DESIGN
    "Informatica di Base" -> "Informatica di Base Fotografia" per FOTOGRAFIA
    etc.

Uso:
    python rename_shared_courses.py --directory "orari"
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict

# Mappatura corsi condivisi -> nomi specifici per corso di studio
SHARED_COURSES_MAP = {
    'DESIGN': {
        'Informatica di Base': 'Informatica di Base Design',
    },
    'FOTOGRAFIA': {
        'Informatica di Base': 'Informatica di Base Fotografia',
    },
    'PITTURA': {
        'Informatica di Base': 'Informatica di Base Pittura',
    },
    'REGIA': {
        'Informatica di Base': 'Informatica di Base Regia',
    },
    'GRAPHIC_DESIGN': {
        # GD potrebbe non avere Informatica di Base, ma aggiungiamo per sicurezza
    },
    'INTERIOR_DESIGN': {
        # INTERIOR potrebbe non avere Informatica di Base
    },
    'FASHION': {
        # FASHION potrebbe non avere Informatica di Base
    },
    'CINEMA': {
        # CINEMA potrebbe non avere Informatica di Base
    },
}

# Mappatura cartelle -> nomi corsi di studio
CORSO_STUDIO_MAP = {
    'DESIGN': 'DESIGN',
    'FASHION': 'FASHION',
    'CINEMA': 'CINEMA',
    'FOTOGRAFIA': 'FOTOGRAFIA',
    'GD': 'GRAPHIC_DESIGN',
    'INTERIOR': 'INTERIOR_DESIGN',
    'PITTURA': 'PITTURA',
    'REGIA': 'REGIA',
}

def get_corso_studio_from_path(file_path: Path) -> str:
    """Estrae il corso di studio dal percorso del file"""
    parts = file_path.parts
    if len(parts) >= 2:
        folder_name = parts[1]
        return CORSO_STUDIO_MAP.get(folder_name, folder_name)
    return 'UNKNOWN'

def rename_shared_courses(events: List[Dict], corso_studio: str) -> tuple:
    """Rinomina i corsi condivisi in modo specifico per il corso di studio"""
    renamed_map = SHARED_COURSES_MAP.get(corso_studio, {})
    
    if not renamed_map:
        return events, 0  # Nessuna rinomina necessaria
    
    updated = []
    renamed_count = 0
    
    for event in events:
        new_event = event.copy()
        corso_name = event.get('corso', '')
        
        # Controlla se questo corso deve essere rinominato
        if corso_name in renamed_map:
            new_name = renamed_map[corso_name]
            new_event['corso'] = new_name
            renamed_count += 1
        
        updated.append(new_event)
    
    return updated, renamed_count

def process_file(file_path: Path, dry_run: bool = False) -> Dict:
    """Processa un singolo file JSON per rinominare corsi condivisi"""
    print(f"\n📄 Processando: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except Exception as e:
        print(f"❌ Errore caricamento {file_path}: {e}")
        return {'total': 0, 'renamed': 0}
    
    corso_studio = get_corso_studio_from_path(file_path)
    print(f"   Corso di studio: {corso_studio}")
    
    updated_events, renamed_count = rename_shared_courses(events, corso_studio)
    
    if renamed_count > 0:
        print(f"   ✅ Rinominati {renamed_count} eventi")
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(updated_events, f, indent=2, ensure_ascii=False)
    else:
        print(f"   ⏭️  Nessuna rinomina necessaria")
    
    return {'total': len(events), 'renamed': renamed_count}

def process_directory(directory: str, dry_run: bool = False):
    """Processa tutti i file JSON in una directory ricorsivamente"""
    dir_path = Path(directory)
    json_files = list(dir_path.rglob('*.json'))
    
    total_stats = {
        'files': 0,
        'total_events': 0,
        'renamed_events': 0
    }
    
    for json_file in json_files:
        stats = process_file(json_file, dry_run=dry_run)
        total_stats['files'] += 1
        total_stats['total_events'] += stats['total']
        total_stats['renamed_events'] += stats['renamed']
    
    print(f"\n{'='*60}")
    print(f"📊 Riepilogo totale:")
    print(f"   File processati: {total_stats['files']}")
    print(f"   Eventi totali: {total_stats['total_events']}")
    print(f"   Eventi rinominati: {total_stats['renamed_events']}")
    if dry_run:
        print(f"\n⚠️  DRY RUN - Nessun file è stato modificato")
    else:
        print(f"\n✅ Corsi condivisi rinominati con successo!")

def main():
    parser = argparse.ArgumentParser(
        description='Rinomina corsi condivisi in modo specifico per ogni corso di studio'
    )
    parser.add_argument('--directory', help='Directory da processare ricorsivamente (tutti i .json)')
    parser.add_argument('--file', help='File JSON singolo da processare')
    parser.add_argument('--dry-run', action='store_true', help='Simula le modifiche senza salvare i file')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("⚠️  MODALITÀ DRY RUN - Nessun file verrà modificato")
    
    if args.directory:
        print(f"🔍 Processando directory: {args.directory}")
        process_directory(args.directory, dry_run=args.dry_run)
    elif args.file:
        print(f"📄 Processando file: {args.file}")
        file_path = Path(args.file)
        if file_path.is_file():
            process_file(file_path, dry_run=args.dry_run)
        else:
            print(f"❌ Errore: Il file specificato non esiste: {args.file}")
    else:
        parser.print_help()
        print("\n❌ Specificare --directory o --file")

if __name__ == '__main__':
    main()

