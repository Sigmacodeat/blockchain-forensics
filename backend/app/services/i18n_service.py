"""
Internationalisierung-Service für Blockchain-Forensik-Anwendung

Implementiert Mehrsprachigkeit (i18n) für globale Benutzerfreundlichkeit.
"""

import logging
import json
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TranslationManager:
    """Verwaltet Übersetzungen für verschiedene Sprachen"""

    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.supported_languages = ["en", "de", "es", "fr", "zh", "ja", "ko", "ru"]
        self.default_language = "en"
        self.load_translations()

    def load_translations(self):
        """Lädt alle Übersetzungen aus JSON-Dateien"""
        try:
            # Pfad zu den Übersetzungsdateien
            translations_dir = Path(__file__).parent.parent / "translations"

            if not translations_dir.exists():
                logger.warning("Übersetzungs-Verzeichnis nicht gefunden, erstelle Standard-Übersetzungen")
                self._create_default_translations()
                return

            # Lade alle Sprachdateien
            for lang_code in self.supported_languages:
                lang_file = translations_dir / f"{lang_code}.json"
                if lang_file.exists():
                    try:
                        with open(lang_file, 'r', encoding='utf-8') as f:
                            self.translations[lang_code] = json.load(f)
                        logger.info(f"✅ Übersetzungen für {lang_code} geladen")
                    except Exception as e:
                        logger.error(f"❌ Fehler beim Laden der Übersetzungen für {lang_code}: {e}")
                        self.translations[lang_code] = self._get_default_translations_for_language(lang_code)
                else:
                    logger.warning(f"⚠️ Übersetzungsdatei für {lang_code} nicht gefunden")
                    self.translations[lang_code] = self._get_default_translations_for_language(lang_code)

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Übersetzungen: {e}")
            self._create_default_translations()

    def _create_default_translations(self):
        """Erstellt Standard-Übersetzungen wenn keine vorhanden sind"""
        for lang_code in self.supported_languages:
            self.translations[lang_code] = self._get_default_translations_for_language(lang_code)

    def _get_default_translations_for_language(self, lang_code: str) -> Dict[str, Any]:
        """Holt Standard-Übersetzungen für eine Sprache"""
        # Basis-Übersetzungen auf Englisch als Fallback
        base_translations = {
            "common": {
                "loading": "Loading...",
                "error": "Error",
                "success": "Success",
                "warning": "Warning",
                "info": "Information",
                "confirm": "Confirm",
                "cancel": "Cancel",
                "save": "Save",
                "delete": "Delete",
                "edit": "Edit",
                "back": "Back",
                "next": "Next",
                "previous": "Previous",
                "search": "Search",
                "filter": "Filter",
                "sort": "Sort",
                "export": "Export",
                "import": "Import"
            },
            "navigation": {
                "dashboard": "Dashboard",
                "wallets": "Wallets",
                "transactions": "Transactions",
                "analytics": "Analytics",
                "settings": "Settings",
                "profile": "Profile",
                "logout": "Logout"
            },
            "wallet": {
                "balance": "Balance",
                "send": "Send",
                "receive": "Receive",
                "swap": "Swap",
                "bridge": "Bridge",
                "stake": "Stake",
                "unstake": "Unstake",
                "claim": "Claim Rewards",
                "history": "Transaction History",
                "export": "Export Wallet",
                "import": "Import Wallet"
            },
            "defi": {
                "liquidity": "Liquidity",
                "staking": "Staking",
                "farming": "Yield Farming",
                "pools": "Liquidity Pools",
                "apy": "APY",
                "tvl": "TVL",
                "rewards": "Rewards",
                "yield": "Yield",
                "risk": "Risk",
                "opportunity": "Opportunity"
            },
            "nft": {
                "portfolio": "NFT Portfolio",
                "collection": "Collection",
                "rarity": "Rarity",
                "floor_price": "Floor Price",
                "market_cap": "Market Cap",
                "volume": "Volume",
                "traits": "Traits",
                "royalty": "Royalty"
            },
            "crosschain": {
                "swap": "Cross-Chain Swap",
                "bridge": "Bridge",
                "arbitrage": "Arbitrage",
                "routes": "Routes",
                "fees": "Fees",
                "time": "Estimated Time",
                "gas": "Gas Fee"
            },
            "auth": {
                "login": "Login",
                "register": "Register",
                "forgot_password": "Forgot Password",
                "reset_password": "Reset Password",
                "email": "Email",
                "password": "Password",
                "confirm_password": "Confirm Password",
                "two_factor": "Two-Factor Authentication",
                "backup_codes": "Backup Codes"
            },
            "errors": {
                "network": "Network Error",
                "unauthorized": "Unauthorized",
                "forbidden": "Forbidden",
                "not_found": "Not Found",
                "server_error": "Server Error",
                "validation": "Validation Error",
                "insufficient_funds": "Insufficient Funds",
                "transaction_failed": "Transaction Failed"
            }
        }

        # Sprachspezifische Anpassungen
        if lang_code == "de":
            return {
                "common": {
                    "loading": "Lädt...",
                    "error": "Fehler",
                    "success": "Erfolg",
                    "warning": "Warnung",
                    "info": "Information",
                    "confirm": "Bestätigen",
                    "cancel": "Abbrechen",
                    "save": "Speichern",
                    "delete": "Löschen",
                    "edit": "Bearbeiten",
                    "back": "Zurück",
                    "next": "Weiter",
                    "previous": "Zurück",
                    "search": "Suchen",
                    "filter": "Filtern",
                    "sort": "Sortieren",
                    "export": "Exportieren",
                    "import": "Importieren"
                },
                "navigation": {
                    "dashboard": "Dashboard",
                    "wallets": "Wallets",
                    "transactions": "Transaktionen",
                    "analytics": "Analytics",
                    "settings": "Einstellungen",
                    "profile": "Profil",
                    "logout": "Abmelden"
                },
                "wallet": {
                    "balance": "Guthaben",
                    "send": "Senden",
                    "receive": "Empfangen",
                    "swap": "Tauschen",
                    "bridge": "Bridge",
                    "stake": "Staken",
                    "unstake": "Unstaken",
                    "claim": "Belohnungen beanspruchen",
                    "history": "Transaktionsverlauf",
                    "export": "Wallet exportieren",
                    "import": "Wallet importieren"
                },
                "defi": {
                    "liquidity": "Liquidität",
                    "staking": "Staking",
                    "farming": "Yield Farming",
                    "pools": "Liquidity Pools",
                    "apy": "APY",
                    "tvl": "TVL",
                    "rewards": "Belohnungen",
                    "yield": "Rendite",
                    "risk": "Risiko",
                    "opportunity": "Gelegenheit"
                },
                "nft": {
                    "portfolio": "NFT Portfolio",
                    "collection": "Sammlung",
                    "rarity": "Seltenheit",
                    "floor_price": "Mindestpreis",
                    "market_cap": "Marktkapitalisierung",
                    "volume": "Volumen",
                    "traits": "Merkmale",
                    "royalty": "Lizenzgebühr"
                },
                "crosschain": {
                    "swap": "Cross-Chain Swap",
                    "bridge": "Bridge",
                    "arbitrage": "Arbitrage",
                    "routes": "Routen",
                    "fees": "Gebühren",
                    "time": "Geschätzte Zeit",
                    "gas": "Gasgebühr"
                },
                "auth": {
                    "login": "Anmelden",
                    "register": "Registrieren",
                    "forgot_password": "Passwort vergessen",
                    "reset_password": "Passwort zurücksetzen",
                    "email": "E-Mail",
                    "password": "Passwort",
                    "confirm_password": "Passwort bestätigen",
                    "two_factor": "Zwei-Faktor-Authentifizierung",
                    "backup_codes": "Backup-Codes"
                },
                "errors": {
                    "network": "Netzwerkfehler",
                    "unauthorized": "Nicht autorisiert",
                    "forbidden": "Verboten",
                    "not_found": "Nicht gefunden",
                    "server_error": "Serverfehler",
                    "validation": "Validierungsfehler",
                    "insufficient_funds": "Unzureichende Mittel",
                    "transaction_failed": "Transaktion fehlgeschlagen"
                }
            }

        return base_translations

    def translate(self, key: str, language: str = None, **kwargs) -> str:
        """Übersetzt einen Schlüssel in die angegebene Sprache"""
        lang = language or self.default_language

        if lang not in self.translations:
            lang = self.default_language

        # Schlüssel aufteilen (z.B. "common.loading")
        parts = key.split('.')
        current = self.translations[lang]

        # Durch die Schlüssel-Hierarchie navigieren
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                logger.warning(f"Übersetzungsschlüssel '{key}' nicht gefunden für Sprache '{lang}'")
                return key  # Fallback: Schlüssel selbst zurückgeben

        # Wenn das Ergebnis ein String ist, Interpolation anwenden
        if isinstance(current, str):
            try:
                return current.format(**kwargs)
            except KeyError:
                return current

        # Wenn das Ergebnis kein String ist, Schlüssel zurückgeben
        return key

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Holt Liste der unterstützten Sprachen"""
        languages = [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "de", "name": "German", "native_name": "Deutsch"},
            {"code": "es", "name": "Spanish", "native_name": "Español"},
            {"code": "fr", "name": "French", "native_name": "Français"},
            {"code": "zh", "name": "Chinese", "native_name": "中文"},
            {"code": "ja", "name": "Japanese", "native_name": "日本語"},
            {"code": "ko", "name": "Korean", "native_name": "한국어"},
            {"code": "ru", "name": "Russian", "native_name": "Русский"}
        ]
        return languages

    def detect_language(self, accept_language: str = None, user_agent: str = None) -> str:
        """Erkennt die bevorzugte Sprache des Benutzers"""
        if accept_language:
            # Accept-Language header analysieren
            languages = [lang.strip() for lang in accept_language.split(',')]
            for lang in languages:
                lang_code = lang.split(';')[0].split('-')[0].lower()
                if lang_code in self.supported_languages:
                    return lang_code

        # Fallback: Englisch
        return self.default_language

    def add_translation(self, language: str, key: str, value: str):
        """Fügt eine neue Übersetzung hinzu"""
        if language not in self.translations:
            self.translations[language] = {}

        # Schlüssel-Hierarchie erstellen
        parts = key.split('.')
        current = self.translations[language]

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

        # Änderungen speichern
        self._save_translation_file(language)

    def _save_translation_file(self, language: str):
        """Speichert Übersetzungen in JSON-Datei"""
        try:
            translations_dir = Path(__file__).parent.parent / "translations"
            translations_dir.mkdir(exist_ok=True)

            lang_file = translations_dir / f"{language}.json"
            with open(lang_file, 'w', encoding='utf-8') as f:
                json.dump(self.translations[language], f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Übersetzungen für {language}: {e}")

class I18nMiddleware:
    """Middleware für automatische Sprach-Erkennung"""

    def __init__(self, translation_manager: TranslationManager):
        self.translation_manager = translation_manager

    async def detect_and_set_language(self, request, response):
        """Erkennt und setzt die Sprache für die Anfrage"""
        # Sprache aus Accept-Language header erkennen
        accept_language = request.headers.get('accept-language')
        user_agent = request.headers.get('user-agent')

        detected_language = self.translation_manager.detect_language(accept_language, user_agent)

        # Sprache in Session/Cookie speichern
        response.set_cookie(
            key="user_language",
            value=detected_language,
            max_age=30*24*60*60,  # 30 Tage
            httponly=True,
            secure=True,
            samesite="lax"
        )

        return detected_language

    def get_language_from_request(self, request) -> str:
        """Holt Sprache aus Anfrage (Cookie/Session)"""
        # Aus Cookie holen
        language = request.cookies.get('user_language')
        if language and language in self.translation_manager.supported_languages:
            return language

        # Aus Accept-Language header
        accept_language = request.headers.get('accept-language')
        return self.translation_manager.detect_language(accept_language)

# Globaler Translation Manager
translation_manager = TranslationManager()
i18n_middleware = I18nMiddleware(translation_manager)

# Hilfsfunktionen für Templates
def t(key: str, language: str = None, **kwargs) -> str:
    """Shortcut für Übersetzung"""
    return translation_manager.translate(key, language, **kwargs)

def get_current_language(request) -> str:
    """Holt aktuelle Sprache aus Request"""
    return i18n_middleware.get_language_from_request(request)
