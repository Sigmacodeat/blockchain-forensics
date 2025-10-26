#!/usr/bin/env python3
"""
Apply Real Product Translations for Top-12 Languages
"""

import json
import os

# Top-12 Sprachen
TOP_LANGUAGES = ['de', 'es', 'fr', 'it', 'pt', 'ru', 'zh', 'ja', 'ko', 'ar', 'hi']

# Produkt-spezifische Übersetzungen
PRODUCT_TRANSLATIONS = {
    "wallet-guardian": {
        "hero": {
            "headline": {
                "de": "Web3 Wallet Guardian: Echtzeit-Krypto-Sicherheit",
                "es": "Web3 Wallet Guardian: Seguridad de Cripto en Tiempo Real",
                "fr": "Web3 Wallet Guardian: Sécurité Crypto en Temps Réel",
                "it": "Web3 Wallet Guardian: Sicurezza Crypto in Tempo Reale",
                "pt": "Web3 Wallet Guardian: Segurança de Crypto em Tempo Real",
                "ru": "Web3 Wallet Guardian: Защита Крипто в Реальном Времени",
                "zh": "Web3钱包守护者：实时加密安全",
                "ja": "Web3ウォレットガーディアン：リアルタイム暗号セキュリティ",
                "ko": "Web3 지갑 가디언: 실시간 암호화 보안",
                "ar": "حارس محفظة Web3: أمان العملات المشفرة في الوقت الفعلي",
                "hi": "Web3 वॉलेट गार्डियन: रीयल-टाइम क्रिप्टो सुरक्षा"
            },
            "subheadline": {
                "de": "Bedrohungen erkennen, bevor sie zuschlagen. Schützen Sie Ihr Krypto mit unternehmensweiter Sicherheit.",
                "es": "Detecta amenazas antes de que ataquen. Protege tu crypto con seguridad empresarial.",
                "fr": "Détecte les menaces avant qu'elles ne frappent. Protège ta crypto avec une sécurité d'entreprise.",
                "it": "Rileva le minacce prima che colpiscano. Proteggi la tua crypto con sicurezza aziendale.",
                "pt": "Detecta ameaças antes que ataquem. Proteja seu crypto com segurança empresarial.",
                "ru": "Обнаруживайте угрозы до того, как они ударят. Защищайте свою крипту корпоративной безопасностью.",
                "zh": "在威胁发生前检测。使用企业级安全保护您的加密货币。",
                "ja": "脅威が襲う前に検知。エンタープライズレベルのセキュリティで暗号を保護。",
                "ko": "위협이 발생하기 전에 감지. 엔터프라이즈급 보안으로 암호화폐를 보호하세요.",
                "ar": "اكتشف التهديدات قبل أن تضرب. احمِ عملاتك المشفرة بأمان المؤسسات.",
                "hi": "धमकियों का पता लगाएं इससे पहले कि वे आएं। एंटरप्राइज़-लेवल सुरक्षा के साथ अपनी क्रिप्टो को सुरक्षित रखें।"
            }
        },
        "features": {
            "title": {
                "de": "Erweiterte Sicherheitsfunktionen",
                "es": "Características de Seguridad Avanzadas",
                "fr": "Fonctionnalités de Sécurité Avancées",
                "it": "Caratteristiche di Sicurezza Avanzate",
                "pt": "Recursos de Segurança Avançados",
                "ru": "Расширенные Функции Безопасности",
                "zh": "高级安全功能",
                "ja": "高度なセキュリティ機能",
                "ko": "고급 보안 기능",
                "ar": "الميزات الأمنية المتقدمة",
                "hi": "उन्नत सुरक्षा सुविधाएं"
            },
            "items": [
                {
                    "title": {
                        "de": "15 ML-Sicherheitsmodelle",
                        "es": "15 Modelos de Seguridad ML",
                        "fr": "15 Modèles de Sécurité ML",
                        "it": "15 Modelli di Sicurezza ML",
                        "pt": "15 Modelos de Segurança ML",
                        "ru": "15 Моделей Безопасности ML",
                        "zh": "15个ML安全模型",
                        "ja": "15のMLセキュリティモデル",
                        "ko": "15개의 ML 보안 모델",
                        "ar": "15 نموذج أمان ML",
                        "hi": "15 एमएल सुरक्षा मॉडल"
                    },
                    "description": {
                        "de": "Fortschrittliche KI erkennt Betrug, Hacks und verdächtige Aktivitäten",
                        "es": "IA avanzada detecta fraudes, hacks y actividades sospechosas",
                        "fr": "IA avancée détecte les fraudes, hacks et activités suspectes",
                        "it": "IA avanzata rileva frodi, hack e attività sospette",
                        "pt": "IA avançada detecta fraudes, hacks e atividades suspeitas",
                        "ru": "Продвинутая ИИ обнаруживает мошенничество, хаки и подозрительную активность",
                        "zh": "先进AI检测欺诈、黑客和可疑活动",
                        "ja": "高度なAIが詐欺、ハッキング、疑わしい活動を検知",
                        "ko": "고급 AI가 사기, 해킹 및 의심스러운 활동을 감지",
                        "ar": "الذكاء الاصطناعي المتقدم يكشف الاحتيال والاختراق والأنشطة المشبوهة",
                        "hi": "एडवांस्ड AI धोखे, हैक्स और संदिग्ध गतिविधियों का पता लगाती है"
                    }
                }
            ]
        }
    }
}

def apply_product_translations():
    """Apply real translations to product files"""

    for lang in TOP_LANGUAGES:
        for product_slug, product_data in PRODUCT_TRANSLATIONS.items():
            try:
                # Lade bestehende Produkt-Translation-Datei
                file_path = f"products/{product_slug}-translations-{lang}.json"
                if not os.path.exists(file_path):
                    continue

                with open(file_path, 'r', encoding='utf-8') as f:
                    translations = json.load(f)

                # Wende Übersetzungen an
                def apply_translations_recursive(data, translation_data, path=""):
                    if isinstance(translation_data, dict):
                        for key, value in translation_data.items():
                            if key in data and isinstance(data[key], (dict, list)):
                                apply_translations_recursive(data[key], value, f"{path}.{key}")
                            elif lang in translation_data.get(key, {}):
                                data[key] = translation_data[key][lang]
                    elif isinstance(translation_data, list) and isinstance(data, list):
                        for i, item in enumerate(translation_data):
                            if i < len(data) and isinstance(item, dict):
                                apply_translations_recursive(data[i], item, f"{path}[{i}]")

                apply_translations_recursive(translations, product_data)

                # Speichere aktualisierte Datei
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, indent=2, ensure_ascii=False)

                print(f"✅ Applied {lang} translations for {product_slug}")

            except Exception as e:
                print(f"❌ Error processing {product_slug} in {lang}: {e}")

    print(f"\n🎯 Applied real product translations for {len(TOP_LANGUAGES)} high-priority languages")

if __name__ == "__main__":
    apply_product_translations()
    print("\n🎉 PRODUCT TRANSLATIONS COMPLETE!")
    print("✅ Top-12 languages: Real product translations applied")
    print("📝 Products covered: wallet-guardian")
    print("🔄 Next: Expand to all 12 products + remaining languages")
