#!/usr/bin/env python3
"""
Automatisches Übersetzungs-Script für i18n JSON-Dateien
Ersetzt englische/deutsche Texte mit Übersetzungen in der Zielsprache
"""

import json
import os
from pathlib import Path

# Mapping der englischen Keys zu Übersetzungen pro Sprache
TRANSLATIONS = {
    # Serbisch (Kyrillisch)
    "sr": {
        "Coming soon": "Ускоро доступно",
        "This feature is still under development.": "Ова функција је још у развоју.",
        "Learn more": "Сазнај више",
        "Welcome back": "Добродошли назад",
        "Overview": "Преглед",
        "Recent Activity": "Недавне активности",
        "Quick Actions": "Брзе акције",
        "Statistics": "Статистике",
        "Notifications": "Обавештења",
        "Active Cases": "Активни случајеви",
        "Traces Today": "Праћења данас",
        "Alerts": "Упозорења",
        "Uptime": "Време рада",
        "Live Alerts": "Упозорења уживо",
        "All Alerts": "Сва упозорења",
        "Trend Analysis": "Анализа трендова",
        "Detailed Analytics": "Детаљна аналитика",
        "Analytics": "Аналитика",
        "How can I help?": "Како могу да помогнем?",
        "Risk Level": "Ниво ризика",
        "Voice Input (43 Languages)": "Гласовни унос (43 језика)",
        "Funding Rate": "Стопа финансирања",
    },
    # Weitere Sprachen können hier hinzugefügt werden
}

def translate_json_file(file_path: Path, lang_code: str):
    """Übersetzt englische Texte in einer JSON-Datei"""
    
    if lang_code not in TRANSLATIONS:
        print(f"⚠️  Keine Übersetzungen für {lang_code} definiert")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    translations = TRANSLATIONS[lang_code]
    changes = 0
    
    def translate_recursive(obj):
        nonlocal changes
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and value in translations:
                    obj[key] = translations[value]
                    changes += 1
                elif isinstance(value, (dict, list)):
                    translate_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                translate_recursive(item)
    
    translate_recursive(data)
    
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ {file_path.name}: {changes} Übersetzungen")
    else:
        print(f"⏭️  {file_path.name}: Keine Änderungen")

def main():
    locales_dir = Path(__file__).parent.parent / "frontend" / "src" / "locales"
    
    if not locales_dir.exists():
        print(f"❌ Verzeichnis nicht gefunden: {locales_dir}")
        return
    
    # Alle JSON-Dateien verarbeiten
    for json_file in locales_dir.glob("*.json"):
        lang_code = json_file.stem
        
        # Skip English und German
        if lang_code in ["en", "de", "fr"]:
            continue
        
        print(f"\n🔄 Verarbeite {lang_code}...")
        translate_json_file(json_file, lang_code)

if __name__ == "__main__":
    main()
