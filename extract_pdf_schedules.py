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
try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except ImportError:
    # Fallback per Python < 3.9
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        # Fallback finale: usa UTC e aggiungi offset manualmente
        ZoneInfo = None

def parse_time(time_str: str) -> Optional[tuple]:
    """
    Parsa una stringa orario (es: "09:00-11:00" o "9.00-11.00" o "14.00-18.00")
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
    Una cella può contenere più lezioni separate da newline.
    DEBUG: Questa funzione viene chiamata
    Formato per ogni lezione:
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
    current_lesson = {}
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Se la riga è un orario, inizia una nuova lezione
        time_range = parse_time(line)
        if time_range:
            # Se c'era una lezione precedente, aggiungila
            if current_lesson and current_lesson.get('time_range'):
                lessons_from_cell.append(current_lesson)
            
            # Inizia nuova lezione
            current_lesson = {
                'time_range': time_range,
                'corso': None,
                'gruppo': None,
                'docente': None,
                'aula': None
            }
            i += 1
            continue
        
        # Se non abbiamo ancora un orario, salta
        if not current_lesson.get('time_range'):
            i += 1
            continue
        
        line_upper = line.upper()
        
        # Cerca gruppo
        if not current_lesson['gruppo']:
            gruppo = extract_group_from_text(line)
            if gruppo:
                current_lesson['gruppo'] = gruppo
                i += 1
                continue
        
        # Cerca professore (contiene "Prof" in qualsiasi forma) - rimuoviamo tutto e prendiamo solo il cognome
        line_lower = line.lower().strip()
        is_prof_line = 'prof' in line_lower
        
        if not current_lesson['docente'] and is_prof_line:
            # Rimuovi completamente tutto quello che contiene "Prof" (qualsiasi variante)
            # e prendi solo il resto (il cognome)
            docente = line.strip()
            
            # Rimuovi tutto fino al cognome: rimuovi "Prof", "Prof.", "Prof.ssa", "Prof ssa", etc.
            # Pattern che rimuove tutto fino al cognome (dopo eventuali spazi/punti dopo "Prof" e "ssa")
            # Ordine importante: prima rimuovi varianti con "ssa", poi quelle semplici
            # Usa pattern senza ^ per catturare anche se non è all'inizio della stringa
            docente = re.sub(r'.*?Prof\.?\s*ssa\s+', '', docente, flags=re.IGNORECASE).strip()  # "Prof. ssa Nome" -> "Nome"
            docente = re.sub(r'.*?Prof\.ssa\s+', '', docente, flags=re.IGNORECASE).strip()  # "Prof.ssa Nome" -> "Nome"
            docente = re.sub(r'.*?Prof\s+ssa\s+', '', docente, flags=re.IGNORECASE).strip()  # "Prof ssa Nome" -> "Nome"
            docente = re.sub(r'.*?Prof\.\s+', '', docente, flags=re.IGNORECASE).strip()  # "Prof. Nome" -> "Nome"
            docente = re.sub(r'.*?Prof\s+', '', docente, flags=re.IGNORECASE).strip()  # "Prof Nome" -> "Nome"
            
            # Rimuovi anche eventuali "ssa" all'inizio che potrebbero essere rimasti
            docente = re.sub(r'^ssa\s+', '', docente, flags=re.IGNORECASE).strip()
            docente = re.sub(r'^ssa/', '', docente, flags=re.IGNORECASE).strip()
            
            # Rimuovi eventuali parentesi o note
            docente = re.sub(r'\([^)]*\)', '', docente).strip()
            # Rimuovi spazi multipli
            docente = re.sub(r'\s+', ' ', docente).strip()
            
            # Se dopo aver rimosso "Prof" non resta niente o resta solo "ssa", controlla la riga successiva
            docente_clean = docente.lower().strip()
            invalid_docente = (not docente or 
                             docente_clean in ['ssa', 'ssa/', 'ssa/ ', 'ssa\n', 'ssa ', ''] or
                             len(docente_clean) <= 2)
            
            if invalid_docente and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # Se la prossima riga non è un'aula, gruppo, orario o corso, è probabilmente il cognome del docente
                next_line_upper = next_line.upper()
                is_not_aula = not any(keyword in next_line_upper for keyword in ['LAB', 'CONFERENCE', 'MAGNA', 'DIGITAL', 'HUB', 'VISUAL', 'PHOTO', '3D', 'VIA', 'FINLANDIA', 'PITTURA', 'MOVIE', 'HALL'])
                is_not_group = not extract_group_from_text(next_line)
                is_not_time = not parse_time(next_line)
                # Non è un corso se contiene solo caratteri comuni per nomi (lettere, spazi, apostrofi, slash)
                is_likely_name = bool(re.match(r'^[A-Za-zÀ-ÿ\s\'\-/]+$', next_line)) and len(next_line) > 2
                
                if next_line and is_not_aula and is_not_group and is_not_time and is_likely_name:
                    # Prendi il cognome dalla riga successiva
                    docente = next_line.strip()
                    i += 1  # Salta anche la riga successiva
            
            # Se abbiamo un cognome valido, salvalo
            if docente and len(docente.strip()) > 2:
                current_lesson['docente'] = docente.strip()
            i += 1
            continue
        
        # Cerca aula (contiene "lab", "Conference", "Magna", "Digital", etc.)
        if not current_lesson['aula'] and any(keyword in line_upper for keyword in ['LAB', 'CONFERENCE', 'MAGNA', 'DIGITAL', 'HUB', 'VISUAL', 'PHOTO', '3D']):
            aula = line.strip()
            # Rimuovi "(portatili)" se presente ma mantieni il testo
            aula = re.sub(r'\s*\(portatili\)', '', aula, flags=re.IGNORECASE).strip()
            current_lesson['aula'] = aula
            i += 1
            continue
        
        # Il corso è la prima riga significativa dopo l'orario che non è gruppo/professore/aula
        # Può anche essere un numero (anno) che ignoriamo
        if not current_lesson['corso']:
            # Ignora numeri soli (probabilmente anno)
            if line.isdigit() and len(line) == 1:
                i += 1
                continue
            # Ignora se è gruppo
            if extract_group_from_text(line):
                i += 1
                continue
            # Altrimenti è il corso (mantieni case originale, non tutto maiuscolo)
            current_lesson['corso'] = line.strip()
        
        i += 1
    
    # Aggiungi l'ultima lezione se presente
    if current_lesson and current_lesson.get('time_range') and current_lesson.get('corso'):
        lessons_from_cell.append(current_lesson)
    
    return lessons_from_cell

def get_semester_dates(semestre: int, base_year: int = 2024) -> tuple:
    """
    Restituisce le date di inizio e fine semestre
    Assumiamo:
    - 1° semestre: inizio ottobre, fine gennaio
    - 2° semestre: inizio febbraio, fine maggio
    """
    if semestre == 1:
        start = datetime(base_year, 10, 1)  # 1 ottobre
        end = datetime(base_year + 1, 1, 31)  # 31 gennaio
    else:
        start = datetime(base_year + 1, 2, 1)  # 1 febbraio
        end = datetime(base_year + 1, 5, 31)  # 31 maggio
    
    return start, end

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
                    print(f"  🔍 Processando tabella {table_idx + 1} ({len(table)} righe)")
                    if not table or len(table) < 2:
                        print(f"    ⚠️  Tabella troppo piccola o vuota")
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
                    print(f"  🔍 DEBUG: header_row = {header_row}, len(table) = {len(table)}")
                    print(f"  🔍 DEBUG: Continuo con ricerca semestre...")
                    
                    # Trova la riga con il semestre corretto
                    # Cerca "1° SEM" o "2° SEM" nella prima colonna (dopo l'header)
                    semester_row = None
                    search_range = range(header_row + 1, min(header_row + 10, len(table)))
                    print(f"  🔍 Cercando semestre {semestre} nelle righe {list(search_range)}")
                    
                    for row_idx in search_range:
                        row = table[row_idx]
                        if not row or len(row) == 0:
                            continue
                        
                        # Controlla la prima colonna per il semestre
                        first_cell = str(row[0]) if row[0] else ""
                        first_cell_upper = first_cell.upper()
                        print(f"    Riga {row_idx}: prima colonna = {repr(first_cell)}")
                        
                        # Gestisci anche formati con newline (es: "1°\nSEM.")
                        first_cell_normalized = first_cell_upper.replace('\n', ' ').replace('  ', ' ')
                        
                        if semestre == 1 and ('1° SEM' in first_cell_normalized or '1 SEM' in first_cell_normalized or 'PRIMO SEM' in first_cell_normalized or '1° SEM.' in first_cell_normalized):
                            semester_row = row_idx
                            break
                        elif semestre == 2 and ('2° SEM' in first_cell_normalized or '2 SEM' in first_cell_normalized or 'SECONDO SEM' in first_cell_normalized or '2° SEM.' in first_cell_normalized):
                            semester_row = row_idx
                            break
                    
                    if semester_row is None:
                        print(f"  ⏭️  Tabella {table_idx + 1}: Semestre {semestre} non trovato")
                        continue
                    
                    print(f"  ✅ Semestre {semestre} trovato alla riga {semester_row}")
                    
                    # Estrai lezioni da ogni colonna giorno dalla riga del semestre
                    semester_data_row = table[semester_row]
                    for day_name, col_idx in day_columns.items():
                        weekday = get_weekday_number(day_name)
                        if weekday == -1:
                            continue
                        
                        if col_idx >= len(semester_data_row):
                            continue
                        
                        cell_text = str(semester_data_row[col_idx]) if semester_data_row[col_idx] else ""
                        if not cell_text.strip():
                            continue
                        
                        # Parsa contenuto cella (può contenere più lezioni)
                        cell_lessons = parse_cell_content(cell_text)
                        
                        if not cell_lessons:
                            continue
                        
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
    # IMPORTANTE: Gli orari nel PDF sono già in ora locale italiana ma vengono salvati con 1 ora in meno.
    # Aggiungiamo 1 ora per correggere il fuso orario.
    # Le ore sono sempre in ora locale italiana (CET/CEST), quindi aggiungiamo 1 ora per compensare
    start_datetime_naive = date.replace(hour=start_time[0], minute=start_time[1], second=0, microsecond=0)
    end_datetime_naive = date.replace(hour=end_time[0], minute=end_time[1], second=0, microsecond=0)
    
    # Aggiungi 1 ora per correggere il fuso orario
    start_datetime_naive = start_datetime_naive + timedelta(hours=1)
    end_datetime_naive = end_datetime_naive + timedelta(hours=1)
    
    # Converti in timezone-aware usando Europe/Rome (gestisce automaticamente ora legale/solare)
    if ZoneInfo:
        rome_tz = ZoneInfo("Europe/Rome")
        start_datetime = start_datetime_naive.replace(tzinfo=rome_tz)
        end_datetime = end_datetime_naive.replace(tzinfo=rome_tz)
        
        # Formato ISO8601 con timezone corretto
        start_iso = start_datetime.isoformat()
        end_iso = end_datetime.isoformat()
    else:
        # Fallback: calcola offset manualmente (approximativo)
        # Ottobre-Marzo: +01:00 (ora solare), Aprile-Settembre: +02:00 (ora legale)
        month = start_datetime_naive.month
        if 4 <= month <= 9:
            offset = "+02:00"  # Ora legale
        else:
            offset = "+01:00"  # Ora solare
        
        start_iso = start_datetime_naive.strftime(f"%Y-%m-%dT%H:%M:%S{offset}")
        end_iso = end_datetime_naive.strftime(f"%Y-%m-%dT%H:%M:%S{offset}")
    
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

