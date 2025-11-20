#!/usr/bin/env python3
"""
Script batch per processare automaticamente tutti i PDF degli orari
dalla cartella "2025 2026" organizzata per corso.

Uso:
    python process_all_pdfs.py --source "/Users/simone/Desktop/2025 2026" --output "orari" --base-year 2025
"""

import os
import re
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Mappa nomi cartelle corso -> codice indirizzo
COURSE_MAP = {
    'DESIGN': 'DES',
    'CINEMA': 'CINEMA',
    'INTERIOR DESIGN': 'INT',
    'FASHION': 'FD',
    'GD': 'GD',
    'GRAPHIC DESIGN': 'GD',
    'FOTOGRAFIA': 'FOTO',
    'PITTURA': 'PIT',
    'REGIA': 'REGIA',
    'REGIA E VIDEOMAKING': 'REGIA'
}

# Mappa nomi file anno -> numero anno
YEAR_MAP = {
    'PRIMO ANNO': 1,
    'SECONDO ANNO': 2,
    'TERZO ANNO': 3,
    '1 ANNO': 1,
    '2 ANNO': 2,
    '3 ANNO': 3,
    '1° ANNO': 1,
    '2° ANNO': 2,
    '3° ANNO': 3,
    'PRIMO': 1,
    'SECONDO': 2,
    'TERZO': 3
}

def find_course_code(course_name: str) -> Optional[str]:
    """Trova il codice corso dal nome della cartella"""
    course_upper = course_name.upper()
    for key, code in COURSE_MAP.items():
        if key in course_upper:
            return code
    return None

def find_year_number(file_name: str) -> Optional[int]:
    """Trova il numero anno dal nome del file"""
    file_upper = file_name.upper()
    # Rimuovi estensione
    file_upper = file_upper.replace('.PDF', '')
    
    # Pattern per "1° ANNO FASHION", "2° ANNO FASHION", etc.
    match = re.search(r'(\d+)°\s*ANNO', file_upper)
    if match:
        return int(match.group(1))
    
    for key, year in YEAR_MAP.items():
        if key in file_upper:
            return year
    
    # Prova pattern numerico diretto
    match = re.search(r'\b([123])\s*(?:ANNO|°|°\s*ANNO)', file_upper)
    if match:
        return int(match.group(1))
    
    return None

def find_semester_in_filename(file_name: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Cerca di capire se il file contiene un semestre specifico
    Restituisce (semestre, None) se trovato, altrimenti (None, None) per entrambi
    """
    file_upper = file_name.upper()
    
    if '1 SEM' in file_upper or '1° SEM' in file_upper or 'PRIMO SEM' in file_upper:
        return (1, None)
    elif '2 SEM' in file_upper or '2° SEM' in file_upper or 'SECONDO SEM' in file_upper:
        return (2, None)
    
    # Se non specificato, assume entrambi i semestri
    return (None, None)

def scan_pdfs(source_dir: str) -> List[Dict]:
    """
    Scansiona la cartella source e trova tutti i PDF organizzati per corso/anno
    """
    pdfs = []
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"❌ Cartella non trovata: {source_dir}")
        return pdfs
    
    print(f"📂 Scansionando: {source_dir}\n")
    
    # Scansiona tutte le cartelle corso
    for course_dir in source_path.iterdir():
        if not course_dir.is_dir():
            continue
        
        course_name = course_dir.name
        course_code = find_course_code(course_name)
        
        if not course_code:
            print(f"⚠️  Corso non riconosciuto: {course_name}")
            continue
        
        print(f"📁 {course_name} → {course_code}")
        
        # Cerca PDF nella cartella corso (solo primo livello, no sottocartelle)
        for pdf_file in course_dir.glob("*.pdf"):
            year = find_year_number(pdf_file.name)
            if not year:
                print(f"   ⚠️  Anno non riconosciuto in: {pdf_file.name}")
                continue
            
            semester, _ = find_semester_in_filename(pdf_file.name)
            
            pdfs.append({
                'path': str(pdf_file),
                'course_code': course_code,
                'course_name': course_name,
                'year': year,
                'semester': semester,
                'filename': pdf_file.name
            })
            
            sem_info = f" (Semestre {semester})" if semester else " (Entrambi i semestri)"
            print(f"   ✅ {pdf_file.name} → Anno {year}{sem_info}")
    
    return pdfs

def process_pdf(pdf_info: Dict, output_dir: str, base_year: int, extract_script: str) -> List[str]:
    """
    Processa un singolo PDF e genera i JSON
    Restituisce lista di file JSON generati
    """
    pdf_path = pdf_info['path']
    course_code = pdf_info['course_code']
    year = pdf_info['year']
    semester = pdf_info['semester']
    
    generated_files = []
    
    # Se il PDF contiene un semestre specifico, processalo solo per quello
    if semester:
        output_file = os.path.join(output_dir, f"{course_code.lower()}-{year}-s{semester}.json")
        
        cmd = [
            'python3', extract_script,
            '--pdf', pdf_path,
            '--output', output_file,
            '--indirizzo', course_code,
            '--anno', str(year),
            '--semestre', str(semester),
            '--base-year', str(base_year)
        ]
        
        print(f"\n🔄 Processando: {pdf_info['filename']} → {output_file}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Generato: {output_file}")
            generated_files.append(output_file)
        else:
            print(f"   ❌ Errore:")
            print(result.stderr)
    
    else:
        # Se non specificato, processa entrambi i semestri
        for sem in [1, 2]:
            output_file = os.path.join(output_dir, f"{course_code.lower()}-{year}-s{sem}.json")
            
            cmd = [
                'python3', extract_script,
                '--pdf', pdf_path,
                '--output', output_file,
                '--indirizzo', course_code,
                '--anno', str(year),
                '--semestre', str(sem),
                '--base-year', str(base_year)
            ]
            
            print(f"\n🔄 Processando: {pdf_info['filename']} (Semestre {sem}) → {output_file}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"   ✅ Generato: {output_file}")
                generated_files.append(output_file)
            else:
                print(f"   ❌ Errore semestre {sem}:")
                print(result.stderr)
    
    return generated_files

def merge_semesters_for_course(course_code: str, year: int, output_dir: str, merge_script: str) -> Optional[str]:
    """
    Unisce i due semestri in un unico file per un corso/anno
    """
    s1_file = os.path.join(output_dir, f"{course_code.lower()}-{year}-s1.json")
    s2_file = os.path.join(output_dir, f"{course_code.lower()}-{year}-s2.json")
    output_file = os.path.join(output_dir, f"{course_code.lower()}-{year}.json")
    
    # Verifica che entrambi i file esistano
    if not os.path.exists(s1_file) or not os.path.exists(s2_file):
        return None
    
    cmd = [
        'python3', merge_script,
        '--s1', s1_file,
        '--s2', s2_file,
        '--output', output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"   ✅ Unito: {output_file}")
        return output_file
    else:
        print(f"   ❌ Errore unione:")
        print(result.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Processa automaticamente tutti i PDF degli orari')
    parser.add_argument('--source', required=True, help='Cartella sorgente con i PDF (es: "/Users/simone/Desktop/2025 2026")')
    parser.add_argument('--output', default='orari', help='Cartella di output per i JSON')
    parser.add_argument('--base-year', type=int, default=2025, help='Anno base per le date')
    parser.add_argument('--extract-script', default='extract_pdf_schedules.py', help='Script di estrazione')
    parser.add_argument('--merge-script', default='merge_semesters.py', help='Script di unione semestri')
    parser.add_argument('--skip-merge', action='store_true', help='Salta l\'unione dei semestri')
    
    args = parser.parse_args()
    
    # Crea cartella output
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Verifica script
    if not os.path.exists(args.extract_script):
        print(f"❌ Script di estrazione non trovato: {args.extract_script}")
        return
    
    if not os.path.exists(args.merge_script):
        print(f"❌ Script di unione non trovato: {args.merge_script}")
        return
    
    print("="*80)
    print("🚀 PROCESSAMENTO BATCH PDF ORARI LABA")
    print("="*80)
    print(f"📂 Sorgente: {args.source}")
    print(f"📁 Output: {args.output}")
    print(f"📅 Anno base: {args.base_year}")
    print("="*80 + "\n")
    
    # Scansiona PDF
    pdfs = scan_pdfs(args.source)
    
    if not pdfs:
        print("\n❌ Nessun PDF trovato!")
        return
    
    print(f"\n📊 Trovati {len(pdfs)} PDF da processare\n")
    print("="*80)
    
    # Processa ogni PDF
    all_generated = []
    for pdf_info in pdfs:
        generated = process_pdf(pdf_info, args.output, args.base_year, args.extract_script)
        all_generated.extend(generated)
    
    # Unisci semestri se richiesto
    if not args.skip_merge:
        print("\n" + "="*80)
        print("🔗 UNIONE SEMESTRI")
        print("="*80)
        
        # Raggruppa per corso/anno
        courses_years = {}
        for pdf_info in pdfs:
            key = (pdf_info['course_code'], pdf_info['year'])
            if key not in courses_years:
                courses_years[key] = pdf_info
        
        for (course_code, year), pdf_info in courses_years.items():
            merged = merge_semesters_for_course(course_code, year, args.output, args.merge_script)
            if merged:
                all_generated.append(merged)
    
    print("\n" + "="*80)
    print("✅ COMPLETATO")
    print("="*80)
    print(f"📊 File generati: {len(all_generated)}")
    print(f"📁 Cartella output: {args.output}")

if __name__ == '__main__':
    main()

