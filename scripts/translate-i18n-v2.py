#!/usr/bin/env python3
"""
🌍 I18N Auto-Translation Script v2 (dynamisch)
- Erkennt alle Sprachen im Ordner frontend/public/locales/
- Nutzt de.json als Struktur-Referenz
- Bewahrt Tech-/Startup-Begriffe (Bridge, Mixer, Hash, Dashboard, etc.)
- Übersetzt nur, wo ein Mapping vorhanden ist (keine falschen Automatik-Texte)
- Erstellt konsistente 419-Key Dateien (wie de.json) für alle Sprachen
- Erstellt eine Kurz-Verifikation pro Datei
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALES_DIR = BASE_DIR / 'frontend' / 'public' / 'locales'

# Minimale Übersetzungs-Mappings für Kerntexte (können später ausgebaut werden)
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    'pl': {
        'Advanced Analytics': 'Zaawansowana Analityka',
        'Real-time insights and threat intelligence': 'Informacje w czasie rzeczywistym i analiza zagrożeń',
        'Refresh': 'Odśwież',
    },
    'ru': {
        'Advanced Analytics': 'Расширенная Аналитика',
        'Real-time insights and threat intelligence': 'Информация в реальном времени и анализ угроз',
        'Refresh': 'Обновить',
    },
    'cs': {
        'Advanced Analytics': 'Pokročilá Analytika',
        'Real-time insights and threat intelligence': 'Informace v reálném čase a analýza hrozeb',
        'Refresh': 'Obnovit',
    },
}

TECH_TERMS = [
    'Blockchain','Bitcoin','Ethereum','Solana','Polygon','Hash','TX','FIFO','Bridge','Mixer','NFT','DeFi',
    'Web3','Smart Contract','Tornado Cash','Pool','Chain','CSV','Excel','PDF','JSON','API','ID','USD'
]
STARTUP_TERMS = ['Dashboard','Analytics','Investigator','Explorer']


def load_reference_translation(lang: str) -> Dict[str, Any]:
    path = LOCALES_DIR / f'{lang}.json'
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_target_languages() -> List[str]:
    """Erkennt alle Sprachcodes im locales/-Ordner.
    Berücksichtigt sowohl vorhandene *.json Dateien als auch reine Ordnernamen.
    """
    langs: List[str] = []
    for entry in sorted(os.listdir(LOCALES_DIR)):
        p = LOCALES_DIR / entry
        if entry.endswith('.json'):
            langs.append(entry[:-5])
        elif p.is_dir():
            langs.append(entry)
    return sorted(set(langs))


def translate_recursive(obj: Any, map_: Dict[str, str]) -> Any:
    if isinstance(obj, dict):
        return {k: translate_recursive(v, map_) for k, v in obj.items()}
    if isinstance(obj, str):
        # Tech-/Startup-Begriffe schützen
        for term in TECH_TERMS + STARTUP_TERMS:
            if term in obj:
                return obj
        # bekannte Übersetzungen anwenden
        return map_.get(obj, obj)
    return obj


def generate(lang: str, ref: Dict[str, Any]) -> Dict[str, Any]:
    map_ = TRANSLATIONS.get(lang, {})
    return translate_recursive(ref, map_)


def quick_verify(lang: str, data: Dict[str, Any]) -> str:
    required = ['analytics','bridge','patterns','cases','automation','privacyDemixing','address','trace']
    for s in required:
        if s not in data:
            return f'⚠️ fehlender Bereich: {s}'
    # simple key count
    def count_keys(o: Any) -> int:
        if isinstance(o, dict):
            return sum(count_keys(v) for v in o.values())
        return 1
    keys = count_keys(data)
    if keys < 300:
        return f'⚠️ wenig Keys: {keys}'
    return f'✅ {keys} keys'


def main():
    print('🌍 I18N Auto-Translation v2 (dynamic scan)')
    de_ref = load_reference_translation('de')
    langs = list_target_languages()

    # Diese sind bereits manuell korrekt
    skip = {'de','en','es','fr','it','pt','nl'}

    for lang in langs:
        if lang in skip:
            continue

        # Erzeuge ggf. fehlende .json Datei auch wenn nur ein Ordner existiert
        out_path = LOCALES_DIR / f'{lang}.json'
        data = generate(lang, de_ref)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        status = quick_verify(lang, data)
        print(f'  {lang}: {status}')

    print('Fertig.')

if __name__ == '__main__':
    main()
