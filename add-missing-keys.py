#!/usr/bin/env python3
"""
Fügt fehlende breadcrumb.* und dashboard.analytics Keys zu allen Sprachen hinzu
"""
import json
from pathlib import Path

# Übersetzungen für fehlende Keys
MISSING_KEYS = {
    "de": {
        "breadcrumb": {
            "home": "Startseite",
            "features": "Funktionen",
            "about": "Über uns",
            "pricing": "Preise",
            "search": "Suche",
            "dashboards": "Dashboards",
            "monitoring": "Überwachung",
            "legal": "Rechtliches",
            "privacy": "Datenschutz",
            "terms": "AGB",
            "impressum": "Impressum"
        },
        "dashboard": {
            "analytics": "Analytics"
        }
    },
    "en": {
        "breadcrumb": {
            "home": "Home",
            "features": "Features",
            "about": "About",
            "pricing": "Pricing",
            "search": "Search",
            "dashboards": "Dashboards",
            "monitoring": "Monitoring",
            "legal": "Legal",
            "privacy": "Privacy",
            "terms": "Terms",
            "impressum": "Imprint"
        },
        "dashboard": {
            "analytics": "Analytics"
        }
    },
    "fr": {
        "breadcrumb": {
            "home": "Accueil",
            "features": "Fonctionnalités",
            "about": "À propos",
            "pricing": "Tarifs",
            "search": "Recherche",
            "dashboards": "Tableaux de bord",
            "monitoring": "Surveillance",
            "legal": "Mentions légales",
            "privacy": "Confidentialité",
            "terms": "Conditions",
            "impressum": "Mentions légales"
        },
        "dashboard": {
            "analytics": "Analytique"
        }
    },
    "es": {
        "breadcrumb": {
            "home": "Inicio",
            "features": "Características",
            "about": "Acerca de",
            "pricing": "Precios",
            "search": "Buscar",
            "dashboards": "Paneles",
            "monitoring": "Monitoreo",
            "legal": "Legal",
            "privacy": "Privacidad",
            "terms": "Términos",
            "impressum": "Aviso legal"
        },
        "dashboard": {
            "analytics": "Analítica"
        }
    },
    "it": {
        "breadcrumb": {
            "home": "Home",
            "features": "Funzionalità",
            "about": "Chi siamo",
            "pricing": "Prezzi",
            "search": "Cerca",
            "dashboards": "Dashboard",
            "monitoring": "Monitoraggio",
            "legal": "Legale",
            "privacy": "Privacy",
            "terms": "Termini",
            "impressum": "Informazioni legali"
        },
        "dashboard": {
            "analytics": "Analisi"
        }
    },
    "pt": {
        "breadcrumb": {
            "home": "Início",
            "features": "Recursos",
            "about": "Sobre",
            "pricing": "Preços",
            "search": "Pesquisar",
            "dashboards": "Painéis",
            "monitoring": "Monitoramento",
            "legal": "Legal",
            "privacy": "Privacidade",
            "terms": "Termos",
            "impressum": "Imprensa"
        },
        "dashboard": {
            "analytics": "Análise"
        }
    },
    "nl": {
        "breadcrumb": {
            "home": "Home",
            "features": "Functies",
            "about": "Over ons",
            "pricing": "Prijzen",
            "search": "Zoeken",
            "dashboards": "Dashboards",
            "monitoring": "Monitoring",
            "legal": "Juridisch",
            "privacy": "Privacy",
            "terms": "Voorwaarden",
            "impressum": "Colofon"
        },
        "dashboard": {
            "analytics": "Analytics"
        }
    },
    "pl": {
        "breadcrumb": {
            "home": "Strona główna",
            "features": "Funkcje",
            "about": "O nas",
            "pricing": "Cennik",
            "search": "Szukaj",
            "dashboards": "Pulpity",
            "monitoring": "Monitorowanie",
            "legal": "Prawne",
            "privacy": "Prywatność",
            "terms": "Warunki",
            "impressum": "Dane firmy"
        },
        "dashboard": {
            "analytics": "Analityka"
        }
    },
    "ru": {
        "breadcrumb": {
            "home": "Главная",
            "features": "Функции",
            "about": "О нас",
            "pricing": "Цены",
            "search": "Поиск",
            "dashboards": "Панели",
            "monitoring": "Мониторинг",
            "legal": "Правовая информация",
            "privacy": "Конфиденциальность",
            "terms": "Условия",
            "impressum": "Выходные данные"
        },
        "dashboard": {
            "analytics": "Аналитика"
        }
    },
    "sv": {
        "breadcrumb": {
            "home": "Hem",
            "features": "Funktioner",
            "about": "Om oss",
            "pricing": "Priser",
            "search": "Sök",
            "dashboards": "Instrumentpaneler",
            "monitoring": "Övervakning",
            "legal": "Juridiskt",
            "privacy": "Integritet",
            "terms": "Villkor",
            "impressum": "Impressum"
        },
        "dashboard": {
            "analytics": "Analys"
        }
    },
    "fi": {
        "breadcrumb": {
            "home": "Etusivu",
            "features": "Ominaisuudet",
            "about": "Tietoja",
            "pricing": "Hinnoittelu",
            "search": "Haku",
            "dashboards": "Kojelaudat",
            "monitoring": "Valvonta",
            "legal": "Oikeudelliset tiedot",
            "privacy": "Yksityisyys",
            "terms": "Käyttöehdot",
            "impressum": "Yhteystiedot"
        },
        "dashboard": {
            "analytics": "Analytiikka"
        }
    },
    "da": {
        "breadcrumb": {
            "home": "Hjem",
            "features": "Funktioner",
            "about": "Om os",
            "pricing": "Priser",
            "search": "Søg",
            "dashboards": "Dashboards",
            "monitoring": "Overvågning",
            "legal": "Juridisk",
            "privacy": "Privatliv",
            "terms": "Vilkår",
            "impressum": "Kolofon"
        },
        "dashboard": {
            "analytics": "Analyse"
        }
    },
    "ko": {
        "breadcrumb": {
            "home": "홈",
            "features": "기능",
            "about": "소개",
            "pricing": "가격",
            "search": "검색",
            "dashboards": "대시보드",
            "monitoring": "모니터링",
            "legal": "법률",
            "privacy": "개인정보 보호",
            "terms": "이용약관",
            "impressum": "회사정보"
        },
        "dashboard": {
            "analytics": "분석"
        }
    },
    "ja": {
        "breadcrumb": {
            "home": "ホーム",
            "features": "機能",
            "about": "概要",
            "pricing": "価格",
            "search": "検索",
            "dashboards": "ダッシュボード",
            "monitoring": "監視",
            "legal": "法的情報",
            "privacy": "プライバシー",
            "terms": "利用規約",
            "impressum": "会社情報"
        },
        "dashboard": {
            "analytics": "分析"
        }
    },
    "zh-CN": {
        "breadcrumb": {
            "home": "首页",
            "features": "功能",
            "about": "关于",
            "pricing": "价格",
            "search": "搜索",
            "dashboards": "仪表板",
            "monitoring": "监控",
            "legal": "法律",
            "privacy": "隐私",
            "terms": "条款",
            "impressum": "公司信息"
        },
        "dashboard": {
            "analytics": "分析"
        }
    },
    "tr": {
        "breadcrumb": {
            "home": "Ana Sayfa",
            "features": "Özellikler",
            "about": "Hakkında",
            "pricing": "Fiyatlandırma",
            "search": "Ara",
            "dashboards": "Panolar",
            "monitoring": "İzleme",
            "legal": "Yasal",
            "privacy": "Gizlilik",
            "terms": "Şartlar",
            "impressum": "Künye"
        },
        "dashboard": {
            "analytics": "Analitik"
        }
    },
    "uk": {
        "breadcrumb": {
            "home": "Головна",
            "features": "Функції",
            "about": "Про нас",
            "pricing": "Ціни",
            "search": "Пошук",
            "dashboards": "Панелі",
            "monitoring": "Моніторинг",
            "legal": "Правова інформація",
            "privacy": "Конфіденційність",
            "terms": "Умови",
            "impressum": "Вихідні дані"
        },
        "dashboard": {
            "analytics": "Аналітика"
        }
    }
}

# Alle Sprachen (42 total)
ALL_LANGUAGES = [
    "de", "en", "fr", "es", "it", "pt", "nl", "pl", "ru", "cs", "sk", "hu", "ro", "bg",
    "el", "sl", "sr", "bs", "mk", "sq", "lt", "lv", "et", "fi", "sv", "da", "nb", "nn",
    "is", "ga", "mt", "lb", "rm", "uk", "be", "tr", "ar", "hi", "he", "zh-CN", "ja", "ko"
]

def add_missing_keys(file_path, lang_code):
    """Fügt fehlende Keys zu einer JSON-Datei hinzu"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verwende Englisch als Fallback für nicht definierte Sprachen
        translations = MISSING_KEYS.get(lang_code, MISSING_KEYS['en'])
        
        changed = False
        
        # Breadcrumb Keys hinzufügen
        if 'breadcrumb' not in data:
            data['breadcrumb'] = {}
        
        for key, value in translations['breadcrumb'].items():
            if key not in data['breadcrumb']:
                data['breadcrumb'][key] = value
                changed = True
        
        # Dashboard Keys hinzufügen
        if 'dashboard' not in data:
            data['dashboard'] = {}
        
        if 'analytics' not in data['dashboard']:
            data['dashboard']['analytics'] = translations['dashboard']['analytics']
            changed = True
        
        if changed:
            # Speichern
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ Fehler: {e}")
        return False

def main():
    locales_dir = Path("frontend/src/locales")
    success_count = 0
    skipped_count = 0
    
    print(f"🚀 Füge fehlende breadcrumb.* und dashboard.analytics Keys hinzu...")
    print(f"📦 Verarbeite {len(ALL_LANGUAGES)} Sprachen\n")
    
    for lang in ALL_LANGUAGES:
        file_path = locales_dir / f"{lang}.json"
        
        if not file_path.exists():
            print(f"⚠️  {lang}.json nicht gefunden, überspringe")
            continue
        
        print(f"✏️  {lang}.json...", end=" ")
        
        if add_missing_keys(file_path, lang):
            success_count += 1
            print("✅ aktualisiert")
        else:
            skipped_count += 1
            print("⏭️  bereits vollständig")
    
    print(f"\n✅ Fertig!")
    print(f"📊 Aktualisiert: {success_count}/{len(ALL_LANGUAGES)}")
    print(f"⏭️  Übersprungen: {skipped_count}/{len(ALL_LANGUAGES)}")

if __name__ == "__main__":
    main()
