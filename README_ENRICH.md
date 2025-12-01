# Arricchimento Orari con LOGOS

## Script `enrich_with_logos.py`

Questo script collega gli orari estratti dai DOCX con i dati di LOGOS usando `oidCorso`.

### Uso

#### Opzione 1: Con token LOGOS (API diretta)
```bash
python3 enrich_with_logos.py \
  --input "orari/gd-1.json" \
  --output "orari/gd-1-enriched.json" \
  --token "YOUR_LOGOS_BEARER_TOKEN" \
  --save-mapping "logos_mapping.json"
```

#### Opzione 2: Con mappatura locale
```bash
# Prima genera la mappatura (una volta)
python3 enrich_with_logos.py \


  --input "orari/gd-1.json" \
  --output "orari/gd-1-enriched.json" \
  --token "YOUR_TOKEN" \
  --save-mapping "logos_mapping.json"

# Poi usa la mappatura salvata
python3 enrich_with_logos.py \
  --input "orari/gd-1.json" \
  --output "orari/gd-1-enriched.json" \
  --mapping "logos_mapping.json"
```

### Cosa fa

1. **Carica eventi** dal JSON estratto dai DOCX
2. **Carica mappatura** corso → `oidCorso` da:
   - API LOGOS (`/api/Enrollments`) se fornito `--token`
   - File JSON locale se fornito `--mapping`
3. **Fa matching** tra nomi corsi normalizzati e aggiunge `oidCorso` agli eventi
4. **Salva** JSON arricchito con `oidCorso` aggiunto

### Matching

Lo script normalizza i nomi dei corsi (come fa l'app Swift) e cerca:
- Match esatto sul nome normalizzato
- Varianti con/senza anno (es: "GRAPHIC DESIGN 2" → "graphic design 2")
- Varianti con numeri (es: "1", "2", "3")

### Output

Il JSON arricchito avrà `oidCorso` aggiunto a ogni evento:
```json
{
  "corso": "GRAPHIC DESIGN 2",
  "oidCorso": "abc123-def456-ghi789",  // ← Aggiunto da LOGOS
  "anno": 1,
  "docente": "Crescioli",
  ...
}
```

### Note

- I corsi senza match avranno `oidCorso: null`
- Lo script mostra un report dei match/unmatch
- La mappatura può essere salvata e riutilizzata per evitare chiamate API ripetute



