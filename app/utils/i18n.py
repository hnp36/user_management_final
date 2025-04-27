from pathlib import Path
import gettext
import json
import os
from typing import Dict, List

# Directory where the translation files (.mo) are located
LOCALE_DIR = Path(__file__).resolve().parent.parent / "locales"
DEFAULT_LANGUAGE = "en"

# Available languages
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "flag": "🇺🇸", "rtl": False},
    "es": {"name": "Español", "flag": "🇪🇸", "rtl": False},
    "fr": {"name": "Français", "flag": "🇫🇷", "rtl": False},
    "ar": {"name": "العربية", "flag": "🇸🇦", "rtl": True},
    "zh": {"name": "中文", "flag": "🇨🇳", "rtl": False},
}

# Load json translations for API responses
API_TRANSLATIONS: Dict[str, Dict[str, str]] = {}

# Load API translations from JSON files
for lang in SUPPORTED_LANGUAGES.keys():
    try:
        json_path = LOCALE_DIR / lang / "api_messages.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                API_TRANSLATIONS[lang] = json.load(f)
    except Exception as e:
        # You can log the exception for better debugging
        print(f"Error loading {lang} API translations: {e}")
        API_TRANSLATIONS[lang] = {}

def get_translator(lang: str = DEFAULT_LANGUAGE) -> gettext.GNUTranslations:
    """
    Load a gettext translator for the given language.
    Falls back to default language if not found.
    """
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE

    try:
        # Try loading the translation for the requested language
        return gettext.translation("messages", localedir=LOCALE_DIR, languages=[lang])
    except FileNotFoundError:
        # Fallback to the default language if translation file is not found
        try:
            return gettext.translation("messages", localedir=LOCALE_DIR, languages=[DEFAULT_LANGUAGE])
        except FileNotFoundError:
            # Ultimate fallback to NullTranslations when neither file is found
            return gettext.NullTranslations()

def translate_api_message(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """
    Get translation for API messages from JSON translations
    """
    lang = lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE
    
    # Try to get the translation from the requested language
    translation = API_TRANSLATIONS.get(lang, {}).get(key)

    if translation:
        return translation
    
    # Fallback to default language if not found in requested language
    translation = API_TRANSLATIONS.get(DEFAULT_LANGUAGE, {}).get(key)

    if translation:
        return translation

    # Ultimate fallback - return the key itself if no translation is found
    return key

def get_available_languages() -> List[Dict[str, str]]:
    """
    Returns list of available languages with metadata
    """
    return [
        {"code": code, **info}
        for code, info in SUPPORTED_LANGUAGES.items()
    ]

def is_supported_language(lang: str) -> bool:
    """
    Check if language is supported
    """
    return lang in SUPPORTED_LANGUAGES
