#!/usr/bin/env python3
"""
Script per aggiungere il campo 'corsoStudio' a tutti gli eventi negli orari.

Questo campo identifica il corso di studio (DESIGN, FASHION, CINEMA, etc.)
così le lezioni condivise non vengono escluse erroneamente.

Uso:
    python add_corso_studio.py --directory "orari"
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict

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
    """
    Estrae il corso di studio dal percorso del file.
    Es: orari/DESIGN/1/1sem.json -> DESIGN
    """
    parts = file_path.parts
    if len(parts) >= 2:
        folder_name = parts[1]  # DESIGN, FASHION, etc.
        return CORSO_STUDIO_MAP.get(folder_name, folder_name)
    return 'UNKNOWN'

def add_corso_studio_to_events(events: List[Dict], corso_studio: str) -> List[Dict]:
    """Aggiunge il campo 'corsoStudio' a tutti gli eventi"""
    updated = []
    for event in events:
        # Crea una copia per non modificare l'originale
        new_event = event.copy()
        new_event['corsoStudio'] = corso_studio
        updated.append(new_event)
    return updated

def process_file(file_path: Path, dry_run: bool = False) -> Dict:
    """Processa un singolo file JSON per aggiungere corsoStudio"""
    print(f"\n📄 Processando: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            events = json.load(f)
    except Exception as e:
        print(f"❌ Errore caricamento {file_path}: {e}")
        return {'total': 0, 'updated': 0}
    
    corso_studio = get_corso_studio_from_path(file_path)
    print(f"   Corso di studio: {corso_studio}")
    
    # Conta quanti eventi hanno già il campo
    already_has_field = sum(1 for e in events if 'corsoStudio' in e)
    
    if already_has_field == len(events):
        print(f"   ⏭️  Tutti gli eventi hanno già 'corsoStudio'")
        return {'total': len(events), 'updated': 0}
    
    updated_events = add_corso_studio_to_events(events, corso_studio)
    
    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(updated_events, f, indent=2, ensure_ascii=False)
    
    updated_count = len(updated_events) - already_has_field
    print(f"   Eventi totali: {len(events)}")
    print(f"   Eventi aggiornati: {updated_count}")
    
    return {'total': len(events), 'updated': updated_count}

def process_directory(directory: str, dry_run: bool = False):
    """Processa tutti i file JSON in una directory ricorsivamente"""
    dir_path = Path(directory)
    json_files = list(dir_path.rglob('*.json'))
    
    total_stats = {
        'files': 0,
        'total_events': 0,
        'updated_events': 0
    }
    
    for json_file in json_files:
        stats = process_file(json_file, dry_run=dry_run)
        total_stats['files'] += 1
        total_stats['total_events'] += stats['total']
        total_stats['updated_events'] += stats['updated']
    
    print(f"\n{'='*60}")
    print(f"📊 Riepilogo totale:")
    print(f"   File processati: {total_stats['files']}")
    print(f"   Eventi totali: {total_stats['total_events']}")
    print(f"   Eventi aggiornati: {total_stats['updated_events']}")
    if dry_run:
        print(f"\n⚠️  DRY RUN - Nessun file è stato modificato")
    else:
        print(f"\n✅ Campo 'corsoStudio' aggiunto con successo!")

def main():
    parser = argparse.ArgumentParser(
        description='Aggiunge il campo corsoStudio a tutti gli eventi negli orari'
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

