#!/usr/bin/env python3
"""
Validiert, dass definierte Minimal-Schlüssel in ALLEN Locale-Dateien vorhanden sind.
Gibt eine kurze Übersicht und listet fehlende Keys pro Datei.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCALES_DIR = ROOT / 'src' / 'locales'
EN_FILE = LOCALES_DIR / 'en.json'

TARGET_KEYS = [
    'common.language','common.loading','common.search','common.dashboard','common.start_free',
    'common.save','common.cancel','common.error','common.success','common.refresh','common.theme',
    'chat.title','chat.placeholder','chat.send','chat.retry','chat.loading',
    'wizard.title','wizard.next','wizard.prev','wizard.finish',
    'layout.header.title','layout.header.nav.home','layout.header.nav.features','layout.header.nav.pricing','layout.header.nav.docs',
    'layout.footer.company','layout.footer.legal','layout.footer.privacy','layout.footer.terms'
]

def get_nested(d, path):
    cur = d
    for p in path.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur

missing_report = {}

files = sorted([p for p in LOCALES_DIR.glob('*.json')])
for f in files:
    try:
        data = json.loads(f.read_text(encoding='utf-8'))
    except Exception as e:
        missing_report[f.name] = [f'JSON_PARSE_ERROR: {e}']
        continue
    missing = []
    for k in TARGET_KEYS:
        if get_nested(data, k) is None:
            missing.append(k)
    if missing:
        missing_report[f.name] = missing

ok = [name for name in [p.name for p in files] if name not in missing_report]
print(f"Locales OK ({len(ok)}): {', '.join(sorted(ok))}")
print()
if missing_report:
    print("Fehlende Keys:")
    for name, keys in sorted(missing_report.items()):
        print(f"- {name}: {len(keys)} fehlend")
        # nur bis zu 8 Keys anzeigen
        for k in keys[:8]:
            print(f"  • {k}")
        if len(keys) > 8:
            print("  • ...")
else:
    print("Alle Ziel-Schlüssel sind in allen Locales vorhanden.")
