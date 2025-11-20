
# PDF Esempi - Orari LABA

Metti qui i PDF degli orari per analizzarli e adattare lo script di estrazione.

## Struttura PDF

I PDF contengono:
- **Tabella settimanale** con giorni LUN-SAB
- **Due semestri**: 1° SEM. e 2° SEM.
- **Per ogni cella**: orario, corso, gruppo (A/B/C/Y/Z), professore, aula
- Alcuni corsi non hanno gruppo (lezioni per tutti)

## Formato Cella Esempio

```
14.00-18.00
GRAPHIC DESIGN 2
Gruppo C
Prof.ssa Crescioli
Multimedia lab
```

## Come procedere

1. Metti i PDF qui (es: `gd-2-s1.pdf`, `gd-2-s2.pdf`)
2. Esegui lo script per vedere cosa estrae
3. Adatta la logica di parsing in `extract_pdf_schedules.py`

