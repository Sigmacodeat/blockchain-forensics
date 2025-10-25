#!/usr/bin/env python3
"""
✅ I18N Verifikations-Script
Überprüft alle 42 Sprachen auf Vollständigkeit und Korrektheit
"""

import json
import os
from pathlib import Path
from collections import defaultdict

LOCALES_DIR = Path(__file__).parent.parent / 'frontend' / 'src' / 'locales'

def list_languages() -> list[str]:
    """Ermittelt alle verfügbaren Sprachen aus dem src/locales Verzeichnis."""
    return sorted([p.stem for p in LOCALES_DIR.glob('*.json')])

# Tech-Begriffe, die beibehalten werden sollten
TECH_TERMS = [
    'Blockchain', 'Bitcoin', 'Ethereum', 'Hash', 'TX', 
    'Bridge', 'Mixer', 'CSV', 'Excel', 'PDF', 'JSON'
]

def verify_file(lang: str) -> dict:
    """Verifiziert eine Sprachdatei"""
    
    file_path = LOCALES_DIR / f'{lang}.json'
    
    if not file_path.exists():
        return {
            'lang': lang,
            'exists': False,
            'status': '❌ FEHLT',
            'size': 0,
            'keys': 0
        }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Zähle Keys
        def count_keys(obj):
            if isinstance(obj, dict):
                return sum(count_keys(v) for v in obj.values())
            return 1
        
        key_count = count_keys(data)
        file_size = os.path.getsize(file_path)
        
        # Check Hauptbereiche
        required = ['analytics', 'bridge', 'patterns', 'cases', 
                   'automation', 'privacyDemixing', 'address', 'trace']
        missing = [s for s in required if s not in data]
        
        # Check auf englische Texte in nicht-EN Dateien
        has_english = False
        if lang not in ['en']:
            content = json.dumps(data)
            if 'Advanced Analytics' in content or 'Real-time insights' in content:
                has_english = True
        
        # Status bestimmen
        if missing:
            status = f"⚠️  UNVOLLSTÄNDIG ({len(missing)} Bereiche fehlen)"
        elif has_english and lang not in ['en', 'de']:
            status = "⚠️  ENGLISCH GEFUNDEN"
        elif key_count < 300:
            status = f"⚠️  WENIG KEYS ({key_count})"
        else:
            status = "✅ OK"
        
        return {
            'lang': lang,
            'exists': True,
            'status': status,
            'size': file_size,
            'keys': key_count,
            'missing_sections': missing,
            'has_english_text': has_english
        }
        
    except Exception as e:
        return {
            'lang': lang,
            'exists': True,
            'status': f"❌ ERROR: {str(e)}",
            'size': 0,
            'keys': 0
        }

def main():
    print("✅ I18N Verifikations-Report")
    print("=" * 80)
    print()

    results = []

    languages = list_languages()
    print(f"\n📂 Gefundene Sprachen ({len(languages)}): {', '.join(languages)}")
    print("-" * 80)

    for lang in languages:
        result = verify_file(lang)
        results.append(result)

        if result['exists']:
            size_kb = result['size'] / 1024
            print(f"  {lang:8} {result['status']:30} {result['keys']:4} keys  {size_kb:6.1f} KB")
        else:
            print(f"  {lang:8} {result['status']}")
    
    print()
    print("=" * 80)
    print("📊 Zusammenfassung")
    print("=" * 80)
    
    total = len(results)
    ok = len([r for r in results if '✅ OK' in r['status']])
    warnings = len([r for r in results if '⚠️' in r['status']])
    errors = len([r for r in results if '❌' in r['status']])
    
    print(f"\nGesamt: {total} Sprachen")
    print(f"  ✅ OK:        {ok} ({ok/total*100:.1f}%)")
    print(f"  ⚠️  Warnings: {warnings} ({warnings/total*100:.1f}%)")
    print(f"  ❌ Fehler:   {errors} ({errors/total*100:.1f}%)")
    
    # Durchschnittliche Keys
    avg_keys = sum(r['keys'] for r in results if r['exists']) / len([r for r in results if r['exists']])
    print(f"\nDurchschnittliche Keys pro Datei: {avg_keys:.0f}")
    
    # Gesamtgröße
    total_size = sum(r['size'] for r in results) / 1024 / 1024
    print(f"Gesamtgröße aller Übersetzungen: {total_size:.2f} MB")
    
    print()

if __name__ == '__main__':
    main()
