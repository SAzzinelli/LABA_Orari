
#!/usr/bin/env python3
"""
Script per unire i JSON di due semestri in un unico file
"""

import json
import argparse

def main():
    parser = argparse.ArgumentParser(description='Unisce JSON di due semestri')
    parser.add_argument('--s1', required=True, help='File JSON 1° semestre')
    parser.add_argument('--s2', required=True, help='File JSON 2° semestre')
    parser.add_argument('--output', required=True, help='File JSON di output unificato')
    
    args = parser.parse_args()
    
    # Carica entrambi i semestri
    with open(args.s1, 'r', encoding='utf-8') as f:
        s1_data = json.load(f)
    
    with open(args.s2, 'r', encoding='utf-8') as f:
        s2_data = json.load(f)
    
    # Unisci
    merged = s1_data + s2_data
    
    # Ordina per data
    merged.sort(key=lambda x: x.get('start', ''))
    
    # Salva
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Uniti {len(s1_data)} eventi del 1° semestre + {len(s2_data)} eventi del 2° semestre")
    print(f"   Totale: {len(merged)} eventi salvati in {args.output}")

if __name__ == '__main__':
    main()



