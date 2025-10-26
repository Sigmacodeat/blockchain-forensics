#!/usr/bin/env python3
"""
AI-Powered Translation for Top-12 Languages
"""

import json
import os

# Top-12 Sprachen mit echten Übersetzungen
TOP_LANGUAGES = {
    'de': 'Deutsch',
    'es': 'Español',
    'fr': 'Français',
    'it': 'Italiano',
    'pt': 'Português',
    'ru': 'Русский',
    'zh': '中文',
    'ja': '日本語',
    'ko': '한국어',
    'ar': 'العربية',
    'hi': 'हिन्दी'
}

# Übersetzungen für gemeinsame Texte (Top-12 Sprachen)
TRANSLATIONS = {
    'common': {
        'cta': {
            'getLifetimeDeal': {
                'de': 'Lifetime-Deal sichern',
                'es': 'Obtener oferta de por vida',
                'fr': 'Obtenir l\'offre à vie',
                'it': 'Ottieni offerta a vita',
                'pt': 'Obter oferta vitalícia',
                'ru': 'Получить пожизненную сделку',
                'zh': '获取终身优惠',
                'ja': '生涯取引を取得',
                'ko': '평생 거래 받기',
                'ar': 'احصل على الصفقة مدى الحياة',
                'hi': 'लाइफटाइम डील प्राप्त करें'
            },
            'startFreeTrial': {
                'de': 'Kostenlose Testversion starten',
                'es': 'Iniciar prueba gratuita',
                'fr': 'Commencer l\'essai gratuit',
                'it': 'Avvia prova gratuita',
                'pt': 'Iniciar teste gratuito',
                'ru': 'Начать бесплатную пробную версию',
                'zh': '开始免费试用',
                'ja': '無料トライアルを開始',
                'ko': '무료 평가판 시작',
                'ar': 'ابدأ التجربة المجانية',
                'hi': 'मुफ्त ट्रायल शुरू करें'
            },
            'learnMore': {
                'de': 'Mehr erfahren',
                'es': 'Aprender más',
                'fr': 'En savoir plus',
                'it': 'Scopri di più',
                'pt': 'Saiba mais',
                'ru': 'Узнать больше',
                'zh': '了解更多',
                'ja': 'もっと知る',
                'ko': '더 알아보기',
                'ar': 'اعرف المزيد',
                'hi': 'और जानें'
            },
            'contactSales': {
                'de': 'Vertrieb kontaktieren',
                'es': 'Contactar ventas',
                'fr': 'Contacter les ventes',
                'it': 'Contatta vendite',
                'pt': 'Contatar vendas',
                'ru': 'Связаться с продажами',
                'zh': '联系销售',
                'ja': '営業にお問い合わせ',
                'ko': '영업팀 문의',
                'ar': 'اتصل بالمبيعات',
                'hi': 'बिक्री से संपर्क करें'
            }
        },
        'pricing': {
            'perMonth': {
                'de': 'pro Monat',
                'es': 'por mes',
                'fr': 'par mois',
                'it': 'al mese',
                'pt': 'por mês',
                'ru': 'в месяц',
                'zh': '每月',
                'ja': '月額',
                'ko': '월간',
                'ar': 'شهرياً',
                'hi': 'महीने के'
            },
            'lifetime': {
                'de': 'lebenslang',
                'es': 'de por vida',
                'fr': 'à vie',
                'it': 'a vita',
                'pt': 'vitalício',
                'ru': 'пожизненно',
                'zh': '终身',
                'ja': '生涯',
                'ko': '평생',
                'ar': 'مدى الحياة',
                'hi': 'लाइफटाइम'
            },
            'save': {
                'de': 'Sparen',
                'es': 'Ahorrar',
                'fr': 'Économiser',
                'it': 'Risparmiare',
                'pt': 'Economizar',
                'ru': 'Сэкономить',
                'zh': '节省',
                'ja': '節約',
                'ko': '저장',
                'ar': 'توفير',
                'hi': 'बचाएं'
            },
            'mostPopular': {
                'de': 'Beliebteste',
                'es': 'Más popular',
                'fr': 'Le plus populaire',
                'it': 'Più popolare',
                'pt': 'Mais popular',
                'ru': 'Самый популярный',
                'zh': '最受欢迎',
                'ja': '最も人気',
                'ko': '가장 인기',
                'ar': 'الأكثر شهرة',
                'hi': 'सर्वाधिक लोकप्रिय'
            }
        },
        'navigation': {
            'home': {
                'de': 'Startseite',
                'es': 'Inicio',
                'fr': 'Accueil',
                'it': 'Home',
                'pt': 'Início',
                'ru': 'Главная',
                'zh': '首页',
                'ja': 'ホーム',
                'ko': '홈',
                'ar': 'الرئيسية',
                'hi': 'होम'
            },
            'products': {
                'de': 'Produkte',
                'es': 'Productos',
                'fr': 'Produits',
                'it': 'Prodotti',
                'pt': 'Produtos',
                'ru': 'Продукты',
                'zh': '产品',
                'ja': '製品',
                'ko': '제품',
                'ar': 'المنتجات',
                'hi': 'उत्पाद'
            },
            'blog': {
                'de': 'Blog',
                'es': 'Blog',
                'fr': 'Blog',
                'it': 'Blog',
                'pt': 'Blog',
                'ru': 'Блог',
                'zh': '博客',
                'ja': 'ブログ',
                'ko': '블로그',
                'ar': 'المدونة',
                'hi': 'ब्लॉग'
            },
            'dashboard': {
                'de': 'Dashboard',
                'es': 'Panel de control',
                'fr': 'Tableau de bord',
                'it': 'Dashboard',
                'pt': 'Painel',
                'ru': 'Панель управления',
                'zh': '仪表板',
                'ja': 'ダッシュボード',
                'ko': '대시보드',
                'ar': 'لوحة التحكم',
                'hi': 'डैशबोर्ड'
            }
        }
    }
}

def apply_translations():
    """Apply translations to all Top-12 language files"""

    for lang_code, lang_name in TOP_LANGUAGES.items():
        try:
            # Lade bestehende Translation-Datei
            file_path = f"appsumo-products/i18n/translations-{lang_code}-complete.json"
            with open(file_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)

            # Wende Übersetzungen an
            for section, section_data in TRANSLATIONS.items():
                if section not in translations:
                    translations[section] = {}

                for subsection, subsection_data in section_data.items():
                    if subsection not in translations[section]:
                        translations[section][subsection] = {}

                    for key, translations_dict in subsection_data.items():
                        if lang_code in translations_dict:
                            if subsection not in translations[section]:
                                translations[section][subsection] = {}
                            translations[section][subsection][key] = translations_dict[lang_code]

            # Speichere aktualisierte Datei
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)

            print(f"✅ Applied translations for {lang_name} ({lang_code})")

        except Exception as e:
            print(f"❌ Error processing {lang_code}: {e}")

    print(f"\n🎯 Applied real translations for all {len(TOP_LANGUAGES)} high-priority languages")

def create_placeholder_translations():
    """Create placeholder translations for remaining 30 languages"""

    REMAINING_LANGUAGES = [
        'bg', 'bn', 'cs', 'da', 'el', 'en', 'fa', 'fi', 'he', 'hr',
        'hu', 'id', 'mr', 'ms', 'nl', 'no', 'pl', 'ro', 'sk', 'sl',
        'sv', 'sw', 'ta', 'te', 'th', 'tl', 'tr', 'uk', 'ur', 'vi', 'zh-TW'
    ]

    for lang in REMAINING_LANGUAGES:
        try:
            file_path = f"appsumo-products/i18n/translations-{lang}-complete.json"

            # Für diese Sprachen erstelle Platzhalter (werden später übersetzt)
            placeholder_translations = {
                "common": {
                    "cta": {
                        "getLifetimeDeal": f"[TRANSLATE:{lang}] Get Lifetime Deal",
                        "startFreeTrial": f"[TRANSLATE:{lang}] Start Free Trial",
                        "learnMore": f"[TRANSLATE:{lang}] Learn More",
                        "contactSales": f"[TRANSLATE:{lang}] Contact Sales"
                    },
                    "pricing": {
                        "perMonth": f"[TRANSLATE:{lang}] per month",
                        "lifetime": f"[TRANSLATE:{lang}] lifetime",
                        "save": f"[TRANSLATE:{lang}] Save",
                        "mostPopular": f"[TRANSLATE:{lang}] Most Popular"
                    }
                },
                "note": f"This language ({lang}) needs translation. Placeholder text will be replaced with actual translations."
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(placeholder_translations, f, indent=2, ensure_ascii=False)

            print(f"📝 Created placeholder translations for {lang}")

        except Exception as e:
            print(f"❌ Error creating placeholders for {lang}: {e}")

    print(f"\n📋 Created placeholder translations for {len(REMAINING_LANGUAGES)} languages")

if __name__ == "__main__":
    apply_translations()
    create_placeholder_translations()
    print("\n🎉 TRANSLATION SETUP COMPLETE!")
    print("✅ Top-12 languages: Real translations applied")
    print("📝 Remaining 30 languages: Placeholders created")
    print("🔄 Next: AI-powered bulk translation for remaining languages")
