#!/usr/bin/env python3
"""
Backfill: Füllt minimale i18n-Schlüssel (ca. 10%) in allen Locale-Dateien auf.
Ziel-Keys: common (Basis-UI), chat (title, placeholder), wizard (title, next/back), layout (header/footer)
Strategie: Fehlende Keys werden aus en.json übernommen. Existierende Keys bleiben unberührt.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / 'src' / 'locales'
EN_FILE = LOCALES_DIR / 'en.json'

# Ziel-Key-Pfade (nur diese werden aufgefüllt)
TARGET_PATHS = [
    # common essentials
    'common.language','common.loading','common.search','common.dashboard','common.start_free',
    'common.save','common.cancel','common.error','common.success','common.refresh','common.theme',
    # chat minimal
    'chat.title','chat.placeholder','chat.send','chat.retry','chat.loading',
    # wizard minimal
    'wizard.title','wizard.next','wizard.prev','wizard.finish',
    # layout minimal
    'layout.header.title','layout.header.nav.home','layout.header.nav.features','layout.header.nav.pricing','layout.header.nav.docs',
    'layout.footer.company','layout.footer.legal','layout.footer.privacy','layout.footer.terms'
]

# Hilfsfunktionen

def get_nested(d, path):
    cur = d
    for p in path.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur

def set_nested(d, path, value):
    parts = path.split('.')
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    if parts[-1] not in cur:
        cur[parts[-1]] = value

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if not EN_FILE.exists():
        raise SystemExit('en.json nicht gefunden')
    en = load_json(EN_FILE)

    files = sorted([p for p in LOCALES_DIR.glob('*.json') if p.name != 'en.json'])
    updated = 0
    for f in files:
        try:
            data = load_json(f)
        except Exception as e:
            print(f"⚠️  {f.name}: JSON_PARSE_ERROR -> {e}")
            continue
        inserted = 0
        for k in TARGET_PATHS:
            en_val = get_nested(en, k)
            if en_val is None:
                continue
            cur_val = get_nested(data, k)
            if cur_val is None:
                set_nested(data, k, en_val)
                inserted += 1
        if inserted:
            save_json(f, data)
            updated += 1
            print(f"✓ {f.name}: +{inserted} Keys ergänzt")
    print(f"\nFertig. {updated} Dateien aktualisiert.")

if __name__ == '__main__':
    main()
