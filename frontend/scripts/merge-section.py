#!/usr/bin/env python3
"""
Merge a top-level section from en.json into target locale files.
Usage: python3 scripts/merge-section.py <section> <locale1> <locale2> ...
If the section exists in target, missing nested keys are filled from en.json (non-destructive).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / 'src' / 'locales'
EN_FILE = LOCALES_DIR / 'en.json'

def deep_merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict):
            if k not in dst or not isinstance(dst.get(k), dict):
                dst[k] = {}
            deep_merge(dst[k], v)
        else:
            if k not in dst:
                dst[k] = v


def main():
    if len(sys.argv) < 3:
        print('Usage: python3 scripts/merge-section.py <section> <locale1> <locale2> ...')
        sys.exit(1)
    section = sys.argv[1]
    targets = sys.argv[2:]

    en = json.loads(EN_FILE.read_text(encoding='utf-8'))
    if section not in en:
        print(f"Section '{section}' not found in en.json")
        sys.exit(2)
    en_section = en[section]

    for loc in targets:
        loc_file = LOCALES_DIR / f"{loc}.json"
        if not loc_file.exists():
            print(f"⚠️  {loc}.json not found, skipping")
            continue
        try:
            data = json.loads(loc_file.read_text(encoding='utf-8'))
        except Exception as e:
            print(f"⚠️  {loc}.json parse error: {e}")
            continue
        if section not in data:
            data[section] = {}
        deep_merge(data[section], en_section)
        loc_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"✓ {loc}.json: merged section '{section}'")

if __name__ == '__main__':
    main()
