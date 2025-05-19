import os
import json
import tkinter as tk

class I18n:
    """
    Simple internationalization class for handling translations
    """

    def __init__(self, default_lang="en"):
        self.translations = {}
        self.current_lang = default_lang
        self.load_translations()

    def load_translations(self):
        """
        Load all translation files from translations directory
        """
        translations_dir = os.path.join(os.getcwd(), "translations")
        os.makedirs(translations_dir, exist_ok=True)

        # Create default translation files if they don't exist
        self._create_default_translation_files(translations_dir)

        # Load all translation files
        for filename in os.listdir(translations_dir):
            if filename.endswith(".json"):
                lang_code = filename.split(".")[0]
                with open(os.path.join(translations_dir, filename), 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)

    def _create_default_translation_files(self, translations_dir):
        """
        Create default translation files if they don't exist
        """
        # English translations
        en_file = os.path.join(translations_dir, "en.json")
        if not os.path.exists(en_file):
            with open(en_file, 'w', encoding='utf-8') as f:
                json.dump(self._get_english_translations(), f, ensure_ascii=False, indent=4)

        # Ukrainian translations
        uk_file = os.path.join(translations_dir, "uk.json")
        if not os.path.exists(uk_file):
            with open(uk_file, 'w', encoding='utf-8') as f:
                json.dump(self._get_ukrainian_translations(), f, ensure_ascii=False, indent=4)

    def _get_english_translations(self):
        # English translations dictionary
        return {
            "monitor_tab": "Monitoring",
            "settings_tab": "Settings",
            # ... other English translations
        }

    def _get_ukrainian_translations(self):
        # Ukrainian translations dictionary
        return {
            "monitor_tab": "Моніторинг",
            "settings_tab": "Налаштування",
            # ... other Ukrainian translations
        }

    def set_language(self, lang_code):
        """
        Set the current language
        """
        if lang_code in self.translations:
            self.current_lang = lang_code
            return True
        return False

    def get(self, key, *args):
        """
        Get translated text for the key in the current language
        """
        # Get translation for the key, or fallback to English, or fallback to the key itself
        translation = self.translations.get(self.current_lang, {}).get(key)
        if translation is None:
            translation = self.translations.get("en", {}).get(key, key)

        # Format with args if provided
        if args and isinstance(translation, str):
            return translation.format(*args)

        return translation


# Create global instance
i18n = I18n()


# Function to get translated text
def get_text(key, *args):
    """
    Get translated text based on the current language
    """
    return i18n.get(key, *args)