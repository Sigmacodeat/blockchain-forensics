#!/usr/bin/env python3
"""
Deep-merge: Ergänzt ALLE fehlenden Keys aus en.json in alle Locale-Dateien.
Nicht-destruktiv: vorhandene Übersetzungen werden NICHT überschrieben.
Ziel: 100% renderbar in allen Sprachen (Fallback-Inhalte = EN, bis native Übersetzung folgt).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / 'src' / 'locales'
EN_FILE = LOCALES_DIR / 'en.json'


def deep_merge_missing(dst, src):
    for k, v in src.items():
        if isinstance(v, dict):
            if k not in dst or not isinstance(dst.get(k), dict):
                dst.setdefault(k, {})
            deep_merge_missing(dst[k], v)
        else:
            if k not in dst:
                dst[k] = v


def main():
    en = json.loads(EN_FILE.read_text(encoding='utf-8'))
    updated_files = 0
    for loc_file in sorted(LOCALES_DIR.glob('*.json')):
        if loc_file.name == 'en.json':
            continue
        try:
            data = json.loads(loc_file.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"⚠️  {loc_file.name}: JSON_PARSE_ERROR -> {e}")
            continue
        before = json.dumps(data, sort_keys=True)
        deep_merge_missing(data, en)
        after = json.dumps(data, sort_keys=True)
        if before != after:
            loc_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            updated_files += 1
            print(f"✓ {loc_file.name}: deep-merged missing keys from en.json")
    print(f"\nFertig. {updated_files} Dateien aktualisiert.")

if __name__ == '__main__':
    main()
