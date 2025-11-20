# Guida Estrazione Orari da PDF

## Setup

1. Installa Python 3.8+ se non ce l'hai
2. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## Struttura PDF

I PDF degli orari sono organizzati per:
- **Corso** (es: Design, Interior Design, Cinema)
- **Anno** (1, 2, 3)
- **Semestre** (1 o 2)
- **Gruppo** (A, B, C, Y, Z - varia per corso/anno)

## Uso Base

```bash
python extract_pdf_schedules.py \
  --pdf "path/to/orario_design_1_1.pdf" \
  --output "orari/des-1.json" \
  --indirizzo "DES" \
  --anno 1 \
  --semestre 1
```

## Processo Completo

### 1. Analizza un PDF di esempio

Prima di tutto, esegui lo script su un PDF per vedere cosa estrae:

```bash
python extract_pdf_schedules.py \
  --pdf "esempio_orario.pdf" \
  --output "test.json" \
  --indirizzo "DES" \
  --anno 1 \
  --semestre 1
```

Lo script stamperà:
- Il testo estratto dal PDF
- Le tabelle trovate
- Un'anteprima per capire la struttura

### 2. Adatta la logica di parsing

Apri `extract_pdf_schedules.py` e modifica la funzione `extract_lessons_from_pdf()` per:
- Riconoscere la struttura delle tabelle nel tuo PDF
- Estrarre: corso, giorno, orario, aula, docente, gruppo
- Gestire i diversi formati (alcuni PDF hanno tabelle, altri testo libero)

### 3. Processa tutti i PDF

Crea uno script batch o esegui manualmente per ogni PDF:

```bash
# Design
python extract_pdf_schedules.py --pdf "orari_pdf/design_1_s1.pdf" --output "orari/des-1.json" --indirizzo "DES" --anno 1 --semestre 1
python extract_pdf_schedules.py --pdf "orari_pdf/design_2_s1.pdf" --output "orari/des-2.json" --indirizzo "DES" --anno 2 --semestre 1
# ... etc
```

### 4. Unisci semestri (opzionale)

Se hai semestri separati, puoi unire i JSON:

```python
import json

# Carica entrambi i semestri
with open('orari/des-1-s1.json') as f:
    s1 = json.load(f)
with open('orari/des-1-s2.json') as f:
    s2 = json.load(f)

# Unisci
merged = s1 + s2

# Salva
with open('orari/des-1.json', 'w') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
```

## Formato Output JSON

Ogni evento ha questa struttura:

```json
{
  "corso": "Nome Corso",
  "oidCorso": null,
  "oidCorsi": null,
  "anno": 1,
  "gruppo": "A",
  "aula": "Aula 101",
  "docente": "Nome Docente",
  "start": "2024-10-01T09:00:00+02:00",
  "end": "2024-10-01T11:00:00+02:00",
  "note": null
}
```

**Campo `gruppo`**:
- `"A"`, `"B"`, `"C"`, `"Y"`, `"Z"` se la lezione è per un gruppo specifico
- `null` se la lezione è per tutti i gruppi

## Note

- Le date devono essere in formato ISO8601 con timezone
- Il campo `gruppo` è opzionale (null se per tutti)
- Alcuni corsi hanno solo gruppo A, altri A+B, altri A+B+C
- Graphic Design e Fashion Design possono avere anche Y e Z per alcuni corsi specifici

## Troubleshooting

**Problema**: Lo script non estrae nulla
- **Soluzione**: Controlla l'anteprima del testo estratto e adatta la logica di parsing

**Problema**: Le date sono sbagliate
- **Soluzione**: Modifica `parse_date()` per riconoscere il formato delle date nei tuoi PDF

**Problema**: I gruppi non vengono riconosciuti
- **Soluzione**: Adatta `extract_group_from_text()` al formato dei tuoi PDF

