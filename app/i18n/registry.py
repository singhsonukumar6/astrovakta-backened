"""Translation registry — loads and provides access to all language translations."""
from typing import Dict, Optional

# Lazy-loaded translation cache: {lang_code: {category: {english: translated}}}
_cache: Dict[str, Dict[str, Dict[str, str]]] = {}


def _load_language(lang: str) -> Dict[str, Dict[str, str]]:
    """Dynamically import and return translation data for a language."""
    if lang in _cache:
        return _cache[lang]

    try:
        if lang == "hi":
            from .translations.hi import TRANSLATIONS
        elif lang == "ta":
            from .translations.ta import TRANSLATIONS
        elif lang == "te":
            from .translations.te import TRANSLATIONS
        elif lang == "kn":
            from .translations.kn import TRANSLATIONS
        elif lang == "ml":
            from .translations.ml import TRANSLATIONS
        elif lang == "bn":
            from .translations.bn import TRANSLATIONS
        elif lang == "mr":
            from .translations.mr import TRANSLATIONS
        elif lang == "gu":
            from .translations.gu import TRANSLATIONS
        elif lang == "pa":
            from .translations.pa import TRANSLATIONS
        else:
            _cache[lang] = {}
            return {}
    except ImportError:
        _cache[lang] = {}
        return {}

    _cache[lang] = TRANSLATIONS
    return TRANSLATIONS


def get_category_translations(lang: str, category: str) -> Dict[str, str]:
    """Get all translations for a category in a given language.

    Categories: tithi, nakshatra, yoga, karana, zodiac, planet,
                weekday, choghadiya, paksha, moon_phase, hora_planet,
                muhurat_rating, etc.
    """
    if lang == "en":
        return {}
    data = _load_language(lang)
    return data.get(category, {})


def translate_value(lang: str, category: str, english_value: str) -> str:
    """Translate a single English value to the target language.

    Returns the English value if lang is 'en', or if no translation found.
    """
    if lang == "en" or not english_value:
        return english_value
    translations = get_category_translations(lang, category)
    return translations.get(english_value, english_value)
