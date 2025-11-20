#!/usr/bin/env python3
"""
Script per estrarre orari da PDF e convertirli in JSON
per il repository LABA_Orari

Requisiti:
    pip install pdfplumber pandas

Uso:
    python extract_pdf_schedules.py --pdf "path/to/orario.pdf" --output "orari/des-1.json" --indirizzo "DES" --anno 1 --semestre 1
"""

import pdfplumber
import json
import re
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys

def parse_time(time_str: str) -> Optional[tuple]:
    """
    Parsa una stringa orario (es: "09:00-11:00" o "9:00-11:00")
    Restituisce (ora_inizio, minuto_inizio, ora_fine, minuto_fine) o None
    """
    if not time_str:
        return None
    
    # Rimuovi spazi e normalizza
    time_str = time_str.strip().replace(" ", "")
    
    # Pattern: HH:MM-HH:MM o H:MM-H:MM o HH.MM-HH.MM (punti invece di due punti)
    # Prova prima con punti (più comune nei DOCX)
    patterns = [
        r'(\d{1,2})\.(\d{2})\s*-\s*(\d{1,2})\.(\d{2})',  # Formato con . (es: 10.00-13.00)
        r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',  # Formato con : (es: 10:00-13:00)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, time_str)
        if match:
            h1, m1, h2, m2 = map(int, match.groups())
            # Valida orari
            if 0 <= h1 <= 23 and 0 <= m1 <= 59 and 0 <= h2 <= 23 and 0 <= m2 <= 59:
                return (h1, m1, h2, m2)
    
    return None

def parse_date(date_str: str, base_year: int = 2024) -> Optional[datetime]:
    """
    Parsa una data (es: "Lunedì 1 Ottobre" o "01/10")
    Restituisce datetime o None
    """
    if not date_str:
        return None
    
    # Pattern per date italiane
    months_it = {
        'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4,
        'maggio': 5, 'giugno': 6, 'luglio': 7, 'agosto': 8,
        'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
    }
    
    # Prova pattern "GG/MM" o "GG MM"
    date_match = re.search(r'(\d{1,2})[/\s]+(\d{1,2})', date_str)
    if date_match:
        day, month = map(int, date_match.groups())
        try:
            return datetime(base_year, month, day)
        except:
            return None
    
    # Prova pattern "Giorno GG Mese"
    for month_name, month_num in months_it.items():
        pattern = rf'(\d{{1,2}})\s+{month_name}'
        match = re.search(pattern, date_str.lower())
        if match:
            day = int(match.group(1))
            try:
                return datetime(base_year, month_num, day)
            except:
                return None
    
    return None

def extract_group_from_text(text: str) -> Optional[str]:
    """
    Estrae il gruppo (A, B, C, Y, Z) dal testo
    """
    if not text:
        return None
    
    # Cerca pattern "Gruppo A", "GRUPPO B", "gr. C", etc.
    patterns = [
        r'[Gg]ruppo\s*([A-Z])',
        r'[Gg]r\.\s*([A-Z])',
        r'\b([A-Z])\s*[Gg]ruppo',
        r'^([A-Z])\s*[-:]',  # "A -" o "A:"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            group = match.group(1).upper()
            if group in ['A', 'B', 'C', 'Y', 'Z']:
                return group
    
    return None

def parse_cell_content(cell_text: str) -> List[Dict]:
    """
    Parsa il contenuto di una cella della tabella settimanale
    Formato atteso:
    - Orario (es: "14.00-18.00")
    - Corso (es: "GRAPHIC DESIGN 2")
    - Gruppo (es: "Gruppo C" o null)
    - Professore (es: "Prof.ssa Crescioli")
    - Aula (es: "Multimedia lab")
    
    Restituisce lista di lezioni dalla cella
    """
    if not cell_text or not cell_text.strip():
        return []
    
    lines = [l.strip() for l in cell_text.split('\n') if l.strip()]
    if len(lines) < 2:
        return []
    
    lessons_from_cell = []
    

def get_weekday_number(day_name: str) -> int:
    """
    Converte nome giorno italiano in numero (0=Lunedì, 6=Domenica)
    """
    days = {
        'lunedi': 0, 'lunedì': 0, 'lun': 0,
        'martedi': 1, 'martedì': 1, 'mar': 1,
        'mercoledi': 2, 'mercoledì': 2, 'mer': 2,
        'giovedi': 3, 'giovedì': 3, 'gio': 3,
        'venerdi': 4, 'venerdì': 4, 'ven': 4,
        'sabato': 5, 'sab': 5,
        'domenica': 6, 'dom': 6
    }
    return days.get(day_name.lower(), -1)

def extract_lessons_from_pdf(pdf_path: str, indirizzo: str, anno: int, semestre: int, base_year: int = 2024) -> List[Dict]:
    """
    Estrae le lezioni da un PDF di orari settimanali
    Struttura attesa: tabella con giorni LUN-SAB, due semestri
    """
    lessons = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📄 Aprendo PDF: {pdf_path}")
            print(f"📊 Pagine trovate: {len(pdf.pages)}")
            
            # Trova la tabella del semestre corretto
            semester_start, semester_end = get_semester_dates(semestre, base_year)
            print(f"📅 Semestre {semestre}: {semester_start.strftime('%d/%m/%Y')} - {semester_end.strftime('%d/%m/%Y')}")
            
            # Mappa giorni della settimana
            day_names = ['LUNEDI', 'MARTEDI', 'MERCOLEDI', 'GIOVEDI', 'VENERDI', 'SABATO']
            day_indices = {name: i for i, name in enumerate(day_names)}
            
            # Estrai tabelle da tutte le pagine
            for page_num, page in enumerate(pdf.pages):
                tables = page.extract_tables()
                
                if not tables:
                    continue
                
                print(f"\n📋 Pagina {page_num + 1}: Trovate {len(tables)} tabelle")
                
                for table_idx, table in enumerate(tables):
                    if not table or len(table) < 2:
                        continue
                    
                    # Cerca header con giorni della settimana
                    header_row = None
                    for row_idx, row in enumerate(table):
                        if row and any(day in str(row).upper() for day in day_names):
                            header_row = row_idx
                            break
                    
                    if header_row is None:
                        print(f"  ⚠️  Tabella {table_idx + 1}: Header giorni non trovato")
                        continue
                    
                    # Trova indici colonne per ogni giorno
                    header = table[header_row]
                    day_columns = {}
                    for col_idx, cell in enumerate(header):
                        if cell:
                            cell_upper = str(cell).upper()
                            for day_name in day_names:
                                if day_name in cell_upper:
                                    day_columns[day_name] = col_idx
                                    break
                    
                    print(f"  ✅ Giorni trovati: {list(day_columns.keys())}")
                    
                    # Verifica se questa è la tabella del semestre corretto
                    # Cerca "1° SEM" o "2° SEM" nella prima colonna o header
                    is_correct_semester = False
                    for row in table[:header_row + 3]:
                        if row:
                            row_text = ' '.join(str(cell) for cell in row if cell).upper()
                            if semestre == 1 and ('1° SEM' in row_text or '1 SEM' in row_text or 'PRIMO SEM' in row_text):
                                is_correct_semester = True
                                break
                            elif semestre == 2 and ('2° SEM' in row_text or '2 SEM' in row_text or 'SECONDO SEM' in row_text):
                                is_correct_semester = True
                                break
                    
                    if not is_correct_semester and len(tables) > 1:
                        print(f"  ⏭️  Tabella {table_idx + 1}: Salto (semestre diverso)")
                        continue
                    
                    # Estrai lezioni da ogni colonna giorno
                    for day_name, col_idx in day_columns.items():
                        weekday = get_weekday_number(day_name)
                        if weekday == -1:
                            continue
                        
                        # Estrai celle per questo giorno (dopo l'header)
                        for row_idx in range(header_row + 1, len(table)):
                            row = table[row_idx]
                            if not row or col_idx >= len(row):
                                continue
                            
                            cell_text = str(row[col_idx]) if row[col_idx] else ""
                            if not cell_text.strip():
                                continue
                            
                            # Parsa contenuto cella
                            cell_lessons = parse_cell_content(cell_text)
                            
                            # Genera eventi per ogni settimana del semestre
                            current_date = semester_start
                            while current_date <= semester_end:
                                # Trova il primo giorno della settimana corrispondente
                                days_until = (weekday - current_date.weekday()) % 7
                                lesson_date = current_date + timedelta(days=days_until)
                                
                                if lesson_date > semester_end:
                                    break
                                
                                # Crea evento per ogni lezione nella cella
                                for cell_lesson in cell_lessons:
                                    time_range = cell_lesson['time_range']
                                    event = create_lesson_event(
                                        corso=cell_lesson['corso'],
                                        anno=anno,
                                        gruppo=cell_lesson['gruppo'],
                                        aula=cell_lesson['aula'],
                                        docente=cell_lesson['docente'],
                                        date=lesson_date,
                                        start_time=(time_range[0], time_range[1]),
                                        end_time=(time_range[2], time_range[3]),
                                        note=None
                                    )
                                    lessons.append(event)
                                
                                # Passa alla settimana successiva
                                current_date += timedelta(days=7)
            
            print(f"\n✅ Estratte {len(lessons)} lezioni totali")
            
    except Exception as e:
        print(f"❌ Errore durante l'estrazione: {e}")
        import traceback
        traceback.print_exc()
    
    return lessons

def create_lesson_event(corso: str, anno: int, gruppo: Optional[str], aula: Optional[str],
                       docente: Optional[str], date: datetime, start_time: tuple, end_time: tuple,
                       note: Optional[str] = None) -> Dict:
    """
    Crea un evento lezione nel formato JSON richiesto
    """
    # Combina data e orario
    start_datetime = date.replace(hour=start_time[0], minute=start_time[1])
    end_datetime = date.replace(hour=end_time[0], minute=end_time[1])
    
    # Formato ISO8601 con timezone
    start_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")
    if not start_iso.endswith('+02:00') and not start_iso.endswith('+01:00'):
        # Aggiungi timezone se mancante (assumiamo Italia, +02:00 per ora legale)
        start_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S+02:00")
    
    end_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")
    if not end_iso.endswith('+02:00') and not end_iso.endswith('+01:00'):
        end_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S+02:00")
    
    return {
        "corso": corso,
        "oidCorso": None,
        "oidCorsi": None,
        "anno": anno,
        "gruppo": gruppo,
        "aula": aula,
        "docente": docente,
        "start": start_iso,
        "end": end_iso,
        "note": note
    }

def main():
    parser = argparse.ArgumentParser(description='Estrae orari da PDF e genera JSON')
    parser.add_argument('--pdf', required=True, help='Percorso al file PDF')
    parser.add_argument('--output', required=True, help='Percorso file JSON di output')
    parser.add_argument('--indirizzo', required=True, help='Codice indirizzo (DES, INT, CINEMA, etc.)')
    parser.add_argument('--anno', type=int, required=True, help='Anno di corso (1, 2, 3)')
    parser.add_argument('--semestre', type=int, default=1, help='Semestre (1 o 2)')
    parser.add_argument('--base-year', type=int, default=2024, help='Anno base per le date')
    
    args = parser.parse_args()
    
    print("🚀 Estrazione orari da PDF")
    print(f"   PDF: {args.pdf}")
    print(f"   Output: {args.output}")
    print(f"   Indirizzo: {args.indirizzo}, Anno: {args.anno}, Semestre: {args.semestre}")
    print("="*80)
    
    # Estrai lezioni
    lessons = extract_lessons_from_pdf(args.pdf, args.indirizzo, args.anno, args.semestre, args.base_year)
    
    # Salva JSON
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(lessons, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Salvati {len(lessons)} eventi in {args.output}")
    
    if len(lessons) == 0:
        print("\n⚠️  Nessun evento estratto. Controlla:")
        print("   1. Il formato del PDF")
        print("   2. La logica di parsing in extract_lessons_from_pdf()")
        print("   3. L'anteprima del testo estratto sopra")

if __name__ == '__main__':
    main()

