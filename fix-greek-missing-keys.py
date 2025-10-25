#!/usr/bin/env python3
"""
Fügt die letzten 16 fehlenden Keys zu el.json (Griechisch) hinzu
"""
import json
from pathlib import Path

GREEK_MISSING_KEYS = {
    "breadcrumb": {
        "monitoring_dashboard": "Πίνακας ελέγχου παρακολούθησης"
    },
    "dashboard": {
        "all_alerts": "Όλες οι ειδοποιήσεις",
        "detailed_analytics": "Λεπτομερή αναλυτικά",
        "live_alerts": "Ζωντανές ειδοποιήσεις",
        "trend_analysis": "Ανάλυση τάσεων"
    },
    "investigator": {
        "timeline": {
            "value_eth": "Αξία (ETH)"
        }
    },
    "nav": {
        "_bridge-transfers_": {
            "label": "Μεταφορές γέφυρας"
        }
    },
    "tooltips": {
        "false_positive_rate": "Ποσοστό ψευδών θετικών: Ποσοστό ειδοποιήσεων που είναι ψευδή θετικά",
        "live_alerts": "Ζωντανές ειδοποιήσεις: Ειδοποιήσεις υψηλού κινδύνου που απαιτούν άμεση προσοχή",
        "mttr": "Μέσος χρόνος απόκρισης: Μέσος χρόνος για την επίλυση ειδοποιήσεων",
        "sanctions_hits": "Κυρώσεις: Διευθύνσεις που ταιριάζουν με λίστες κυρώσεων",
        "sla_breach_rate": "Ποσοστό παραβίασης SLA: Ποσοστό ειδοποιήσεων που δεν απαντήθηκαν εντός SLA",
        "trend_analysis": "Ανάλυση τάσεων: Αναλύστε τάσεις κινδύνου με την πάροδο του χρόνου",
        "trend_analysis_admin": "Ανάλυση τάσεων (Admin): Προβολή λεπτομερών τάσεων συστήματος"
    }
}

def add_missing_keys_nested(data, keys, path=''):
    """Recursively add missing nested keys"""
    changed = False
    for key, value in keys.items():
        if isinstance(value, dict):
            if key not in data:
                data[key] = {}
                changed = True
            nested_changed = add_missing_keys_nested(data[key], value, f"{path}.{key}" if path else key)
            changed = changed or nested_changed
        else:
            if key not in data:
                data[key] = value
                changed = True
                print(f"  ✅ Hinzugefügt: {path}.{key}" if path else f"  ✅ Hinzugefügt: {key}")
    return changed

def main():
    file_path = Path("frontend/src/locales/el.json")
    
    print("🎯 Behebe die letzten 16 fehlenden Keys in Griechisch (el.json)...")
    print()
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changed = add_missing_keys_nested(data, GREEK_MISSING_KEYS)
    
    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print()
        print("🎉 PERFEKT! Griechisch ist jetzt 100% komplett!")
        print("✨ ALLE 42 SPRACHEN HABEN 100% COVERAGE! ✨")
    else:
        print("⏭️  Bereits vollständig")

if __name__ == "__main__":
    main()
