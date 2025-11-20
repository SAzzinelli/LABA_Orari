
# 📋 Istruzioni per l'estrazione orari

## 1. Metti i PDF qui

Copia i PDF degli orari in questa cartella (`pdf_esempi/`).

**Esempio struttura file:**
```
pdf_esempi/
├── gd-2-s1.pdf    (Graphic Design 2° anno, 1° semestre)
├── gd-2-s2.pdf    (Graphic Design 2° anno, 2° semestre)
├── des-1-s1.pdf   (Design 1° anno, 1° semestre)
└── ...
```

## 2. Testa l'estrazione

Esegui lo script su un PDF per vedere cosa estrae:

```bash
cd /Users/simone/Desktop/App\ LABA/LABA_Orari

# Test su un PDF di esempio
python extract_pdf_schedules.py \
  --pdf "pdf_esempi/gd-2-s1.pdf" \
  --output "test-s1.json" \
  --indirizzo "GD" \
  --anno 2 \
  --semestre 1 \
  --base-year 2025
```

Lo script stamperà:
- ✅ Tabelle trovate
- ✅ Giorni riconosciuti (LUN, MAR, MER, GIO, VEN, SAB)
- ✅ Numero di lezioni estratte
- ⚠️ Eventuali problemi

## 3. Verifica il risultato

Apri il file JSON generato (`test-s1.json`) e verifica che:
- ✅ Le date siano corrette
- ✅ Gli orari siano corretti
- ✅ I gruppi (A, B, C, Y, Z) siano estratti correttamente
- ✅ I professori e le aule siano presenti

## 4. Se serve, adatta lo script

Se lo script non estrae correttamente:
1. Controlla l'output dello script (stampa le tabelle trovate)
2. Modifica `parse_cell_content()` se il formato delle celle è diverso
3. Modifica `extract_lessons_from_pdf()` se la struttura della tabella è diversa

## 5. Genera tutti i JSON

Una volta verificato che funziona, genera tutti i file:

```bash
# 1° semestre
python extract_pdf_schedules.py --pdf "pdf_esempi/gd-2-s1.pdf" --output "orari/gd-2-s1.json" --indirizzo "GD" --anno 2 --semestre 1 --base-year 2025

# 2° semestre
python extract_pdf_schedules.py --pdf "pdf_esempi/gd-2-s2.pdf" --output "orari/gd-2-s2.json" --indirizzo "GD" --anno 2 --semestre 2 --base-year 2025

# Poi unisci i semestri (vedi sotto)
```

## 6. Unisci i semestri

Dopo aver generato entrambi i semestri, uniscili in un unico file:

```bash
python merge_semesters.py --s1 "orari/gd-2-s1.json" --s2 "orari/gd-2-s2.json" --output "orari/gd-2.json"
```

Oppure manualmente con Python:

```python
import json

with open('orari/gd-2-s1.json') as f:
    s1 = json.load(f)
with open('orari/gd-2-s2.json') as f:
    s2 = json.load(f)

merged = s1 + s2

with open('orari/gd-2.json', 'w') as f:
    json.dump(merged, f, indent=2, ensure_ascii=False)
```

## 7. Commit e push

```bash
git add orari/*.json
git commit -m "Aggiunti orari per [indirizzo] [anno]"
git push
```

