import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Callable
from functools import lru_cache
from pydantic import BaseModel
import pytz
from datetime import datetime
from fastapi import Request, Depends


class Translation(BaseModel):
    """Model for translations in a specific language"""
    language: str
    translations: Dict[str, str]


class LocalizationManager:
    """
    Manages localization and translations for the application.
    Loads translations from JSON files in the 'locales' directory.
    """
    
    def __init__(self, default_language: str = "en", supported_languages: List[str] = None):
        self.default_language = default_language
        self.supported_languages = supported_languages or ["en"]
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Load translation files
        self._load_translations()
    
    def _load_translations(self):
        """Load all translation files from the locales directory"""
        # Get the locales directory (relative to this file)
        locales_dir = Path(__file__).parent.parent.parent / "locales"
        
        # Ensure the directory exists
        if not locales_dir.exists():
            os.makedirs(locales_dir, exist_ok=True)
            
            # Create default English translation file if it doesn't exist
            en_file = locales_dir / "en.json"
            if not en_file.exists():
                with open(en_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "greeting": "Hello!",
                        "welcome": "Welcome to our application!",
                        "email_verification_subject": "Verify Your Account",
                        "password_reset_subject": "Password Reset Instructions",
                        "account_locked_subject": "Account Locked Notification",
                        "user_not_found": "User not found",
                        "email_already_exists": "Email already exists",
                        "invalid_credentials": "Incorrect email or password",
                        "account_locked": "Account locked due to too many failed login attempts",
                        "invalid_token": "Could not validate credentials",
                        "permission_denied": "Operation not permitted",
                        "email_verified": "Email verified successfully",
                        "invalid_verification_token": "Invalid or expired verification token",
                        "internal_error": "An unexpected error occurred"
                    }, f, indent=2)
        
        # Load each translation file
        for lang_file in locales_dir.glob("*.json"):
            lang_code = lang_file.stem
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.translations[lang_code] = json.load(f)
                
                # Add to supported languages if it's not already there
                if lang_code not in self.supported_languages:
                    self.supported_languages.append(lang_code)
            except Exception as e:
                print(f"Error loading translation file {lang_file}: {e}")
    
    def get_translation(self, key: str, language: str, **kwargs) -> str:
        """
        Get a translation for a specific key in the requested language.
        Falls back to default language if the key is not found.
        
        Args:
            key: The translation key
            language: The language code
            **kwargs: Format parameters for the translation string
            
        Returns:
            The translated string
        """
        # Check if language is supported, otherwise use default
        if not self.is_supported_language(language):
            language = self.default_language
        
        # Try to get translation in requested language
        translation = self.translations.get(language, {}).get(key)
        
        # Fall back to default language if not found
        if translation is None and language != self.default_language:
            translation = self.translations.get(self.default_language, {}).get(key)
        
        # If still not found, return the key itself
        if translation is None:
            return key
        
        # Apply any format parameters
        if kwargs:
            try:
                return translation.format(**kwargs)
            except KeyError:
                # Return unformatted if format fails
                return translation
        
        return translation
    
    def is_supported_language(self, language: str) -> bool:
        """Check if a language is supported by the application"""
        return language in self.supported_languages
    
    def list_supported_languages(self) -> List[str]:
        """Return a list of all supported languages"""
        return self.supported_languages

    def format_datetime(self, dt: datetime, language: str, timezone: str = "UTC", 
                       format_str: Optional[str] = None) -> str:
        """
        Format a datetime object according to the locale and timezone.
        
        Args:
            dt: The datetime object to format
            language: The language code
            timezone: The timezone to convert to
            format_str: Optional format string to override default
            
        Returns:
            Formatted datetime string
        """
        if dt is None:
            return ""
            
        # Convert to specified timezone
        try:
            tz = pytz.timezone(timezone)
            if dt.tzinfo is None:
                # Assume UTC if no timezone info
                dt = pytz.utc.localize(dt)
            
            localized_dt = dt.astimezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            # Fall back to UTC if timezone is unknown
            localized_dt = dt.astimezone(pytz.UTC) if dt.tzinfo else dt
        
        # Format based on language/locale
        if format_str:
            return localized_dt.strftime(format_str)
        
        # Default formats based on language
        if language == "fr":
            return localized_dt.strftime("%d/%m/%Y %H:%M")
        elif language == "de":
            return localized_dt.strftime("%d.%m.%Y %H:%M")
        elif language == "ja":
            return localized_dt.strftime("%Y年%m月%d日 %H:%M")
        else:
            # Default English format
            return localized_dt.strftime("%Y-%m-%d %H:%M:%S %Z")


@lru_cache()
def get_localization_manager() -> LocalizationManager:
    """Dependency to get the LocalizationManager instance"""
    return LocalizationManager()


def get_translator(request: Request, loc_manager: LocalizationManager = Depends(get_localization_manager)):
    """
    Returns a function that can be used to translate messages.
    
    Usage in an endpoint:
        @app.get("/hello")
        async def hello(t = Depends(get_translator)):
            return {"message": t("greeting")}
    """
    language = getattr(request.state, "language", loc_manager.default_language)
    
    def translate(key: str, **kwargs) -> str:
        return loc_manager.get_translation(key, language, **kwargs)
    
    return translate