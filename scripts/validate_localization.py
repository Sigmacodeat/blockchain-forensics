#!/usr/bin/env python3
"""
Validiert Lokalisierung für alle Sprachen:
1. Prüft ob alle Locale-Dateien existieren
2. Prüft ob alle wichtigen Translation-Keys vorhanden sind
3. Prüft ob für alle Währungen Wechselkurse definiert sind
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set

# Wichtige Keys die in ALLEN Locale-Dateien vorhanden sein müssen
REQUIRED_KEYS = [
    'landing.hero.title',
    'landing.hero.subtitle',
    'landing.cta.demo',
    'landing.cta.pricing',
    'pricing.seo.title',
    'pricing.card.per_month',
    'pricing.card.popular',
    'navigation.home',
    'navigation.features',
    'navigation.pricing',
    'common.loading',
    'common.error',
]

# Erwartetete Sprachen (42)
EXPECTED_LANGUAGES = [
    'ar', 'be', 'bg', 'bs', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr', 'ga',
    'hi', 'hu', 'is', 'it', 'ja', 'ko', 'he', 'lb', 'lt', 'lv', 'mk', 'mt', 'nb', 'nl',
    'nn', 'pl', 'pt', 'rm', 'ro', 'ru', 'sk', 'sl', 'sq', 'sr', 'sv', 'tr', 'uk', 'zh-CN'
]

def get_nested_value(data: dict, key_path: str) -> any:
    """Holt verschachtelte Werte aus Dictionary"""
    keys = key_path.split('.')
    value = data
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

def check_locale_file(file_path: Path, required_keys: List[str]) -> Dict[str, any]:
    """Prüft eine Locale-Datei"""
    result = {
        'exists': file_path.exists(),
        'valid_json': False,
        'missing_keys': [],
        'total_keys': 0,
        'error': None
    }
    
    if not result['exists']:
        return result
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        result['valid_json'] = True
        
        # Zähle alle Keys (rekursiv)
        def count_keys(obj):
            count = 0
            if isinstance(obj, dict):
                for value in obj.values():
                    if isinstance(value, dict):
                        count += count_keys(value)
                    else:
                        count += 1
            return count
        
        result['total_keys'] = count_keys(data)
        
        # Prüfe erforderliche Keys
        for key in required_keys:
            value = get_nested_value(data, key)
            if value is None:
                result['missing_keys'].append(key)
    
    except json.JSONDecodeError as e:
        result['error'] = f"Invalid JSON: {e}"
    except Exception as e:
        result['error'] = f"Error: {e}"
    
    return result

def main():
    """Main validation function"""
    # Pfade
    script_dir = Path(__file__).parent
    locales_dir = script_dir.parent / 'frontend' / 'src' / 'locales'
    currency_converter_file = script_dir.parent / 'frontend' / 'src' / 'utils' / 'currencyConverter.ts'
    i18n_context_file = script_dir.parent / 'frontend' / 'src' / 'contexts' / 'I18nContext.tsx'
    
    print("=" * 80)
    print("🌍 LOKALISIERUNGS-VALIDIERUNG")
    print("=" * 80)
    
    # 1. Prüfe Locale-Dateien
    print("\n📁 Prüfe Locale-Dateien...")
    print(f"   Verzeichnis: {locales_dir}")
    print(f"   Erwartete Sprachen: {len(EXPECTED_LANGUAGES)}")
    
    found_languages = []
    missing_languages = []
    results = {}
    
    for lang in EXPECTED_LANGUAGES:
        file_path = locales_dir / f"{lang}.json"
        result = check_locale_file(file_path, REQUIRED_KEYS)
        results[lang] = result
        
        if result['exists']:
            found_languages.append(lang)
        else:
            missing_languages.append(lang)
    
    print(f"   ✅ Gefunden: {len(found_languages)}/{len(EXPECTED_LANGUAGES)}")
    
    if missing_languages:
        print(f"   ❌ Fehlende Dateien: {', '.join(missing_languages)}")
    
    # 2. Prüfe Translation-Keys
    print("\n📝 Prüfe Translation-Keys...")
    
    incomplete_translations = {}
    total_missing = 0
    
    for lang, result in results.items():
        if result['exists'] and result['valid_json']:
            if result['missing_keys']:
                incomplete_translations[lang] = result['missing_keys']
                total_missing += len(result['missing_keys'])
    
    if incomplete_translations:
        print(f"   ⚠️  Unvollständige Übersetzungen: {len(incomplete_translations)} Sprachen")
        print(f"   ❌ Fehlende Keys gesamt: {total_missing}")
        
        # Zeige Details für erste 3 Sprachen
        for i, (lang, missing) in enumerate(list(incomplete_translations.items())[:3]):
            print(f"\n   {lang}: {len(missing)} fehlende Keys")
            for key in missing[:3]:
                print(f"      - {key}")
            if len(missing) > 3:
                print(f"      ... und {len(missing) - 3} weitere")
            if i >= 2:
                break
    else:
        print(f"   ✅ Alle erforderlichen Keys vorhanden in allen Sprachen")
    
    # 3. Prüfe Währungszuordnungen
    print("\n💱 Prüfe Währungszuordnungen...")
    
    # Lese CURRENCY_MAP aus I18nContext.tsx
    currency_map = {}
    if i18n_context_file.exists():
        with open(i18n_context_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Einfaches Parsing (nicht robust, aber funktioniert für unseren Fall)
            in_currency_map = False
            for line in content.split('\n'):
                if 'export const CURRENCY_MAP' in line:
                    in_currency_map = True
                    continue
                if in_currency_map:
                    if '}' in line and not ':' in line:
                        break
                    if ':' in line and "'" in line:
                        parts = line.split("'")
                        if len(parts) >= 4:
                            locale = parts[1]
                            currency = parts[3]
                            currency_map[locale] = currency
    
    print(f"   Gefundene Währungszuordnungen: {len(currency_map)}")
    
    # Lese EXCHANGE_RATES aus currencyConverter.ts
    exchange_rates = set()
    if currency_converter_file.exists():
        with open(currency_converter_file, 'r', encoding='utf-8') as f:
            content = f.read()
            in_exchange_rates = False
            for line in content.split('\n'):
                if 'export const EXCHANGE_RATES' in line:
                    in_exchange_rates = True
                    continue
                if in_exchange_rates:
                    if '}' in line and not ':' in line:
                        break
                    if ':' in line and "'" in line:
                        parts = line.split("'")
                        if len(parts) >= 2:
                            currency = parts[1]
                            exchange_rates.add(currency)
    
    print(f"   Gefundene Wechselkurse: {len(exchange_rates)}")
    
    # Prüfe ob alle Währungen Wechselkurse haben
    unique_currencies = set(currency_map.values())
    missing_rates = unique_currencies - exchange_rates
    
    if missing_rates:
        print(f"   ❌ Währungen ohne Wechselkurs: {', '.join(sorted(missing_rates))}")
    else:
        print(f"   ✅ Alle Währungen haben Wechselkurse")
    
    # 4. Zusammenfassung
    print("\n" + "=" * 80)
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 80)
    
    all_good = True
    
    if missing_languages:
        print(f"❌ Fehlende Locale-Dateien: {len(missing_languages)}")
        all_good = False
    else:
        print(f"✅ Alle {len(EXPECTED_LANGUAGES)} Locale-Dateien vorhanden")
    
    if incomplete_translations:
        print(f"⚠️  Unvollständige Übersetzungen: {len(incomplete_translations)} Sprachen")
        all_good = False
    else:
        print(f"✅ Alle Übersetzungen vollständig")
    
    if missing_rates:
        print(f"❌ Fehlende Wechselkurse: {len(missing_rates)}")
        all_good = False
    else:
        print(f"✅ Alle Wechselkurse definiert")
    
    if all_good:
        print("\n🎉 PERFEKT! Alle Lokalisierungen sind vollständig.")
        print("   Die Plattform ist bereit für den weltweiten Einsatz!")
    else:
        print("\n⚠️  Es gibt noch Lücken in der Lokalisierung.")
        print("   Bitte behebe die oben genannten Probleme.")
    
    print("=" * 80)

if __name__ == '__main__':
    main()
