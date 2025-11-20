# 🚀 Processamento Batch PDF Orari

Script automatico per processare tutti i PDF degli orari dalla cartella organizzata per corso.

## Struttura Attesa

```
2025 2026/
├── DESIGN/
│   ├── PRIMO ANNO.pdf
│   ├── SECONDO ANNO.pdf
│   └── TERZO ANNO.pdf
├── GD/
│   ├── PRIMO ANNO.pdf
│   ├── SECONDO ANNO.pdf
│   └── TERZO ANNO.pdf
├── FASHION/
│   ├── 1° ANNO FASHION.pdf
│   ├── 2° ANNO FASHION.pdf
│   └── 3° ANNO FASHION.pdf
└── ...
```

## Uso

### Processamento Completo Automatico

```bash
cd /Users/simone/Desktop/App\ LABA/LABA_Orari

python process_all_pdfs.py \
  --source "/Users/simone/Desktop/2025 2026" \
  --output "orari" \
  --base-year 2025
```

Lo script:
1. ✅ Scansiona tutte le cartelle corso
2. ✅ Riconosce automaticamente corso e anno dai nomi file
3. ✅ Processa ogni PDF per entrambi i semestri
4. ✅ Genera file JSON separati per semestre
5. ✅ Unisce automaticamente i semestri in file finali

### Opzioni

- `--source`: Cartella con i PDF (default: richiesto)
- `--output`: Cartella output JSON (default: "orari")
- `--base-year`: Anno base per le date (default: 2025)
- `--skip-merge`: Salta l'unione dei semestri

### Esempio Output

```
orari/
├── des-1-s1.json    (1° semestre)
├── des-1-s2.json    (2° semestre)
├── des-1.json        (unificato)
├── gd-2-s1.json
├── gd-2-s2.json
└── gd-2.json
```

## Corsi Supportati

- **DESIGN** → `des`
- **GD / GRAPHIC DESIGN** → `gd`
- **FASHION** → `fd`
- **CINEMA** → `cinema`
- **INTERIOR DESIGN** → `int`
- **FOTOGRAFIA** → `foto`
- **PITTURA** → `pit`
- **REGIA** → `regia`

## Note

- I PDF devono contenere entrambi i semestri (1° SEM. e 2° SEM.)
- Lo script genera eventi per ogni settimana del semestre
- I gruppi (A, B, C, Y, Z) vengono estratti automaticamente
- Se un PDF contiene solo un semestre, usa `--skip-merge` e processa manualmente

