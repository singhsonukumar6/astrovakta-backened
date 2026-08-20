"""Internationalization (i18n) support for AstroVakta API.

Usage:
    from app.i18n import t, detect_language

    # In endpoint handler:
    lang = detect_language(query_lang=body.lang, header_lang=accept_lang)
    response_data["tithi"] = t("tithi", raw_tithi, lang)
"""
from typing import Optional, Dict, Any, Union
from .languages import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from .registry import translate_value, get_category_translations


# Alias for convenience
t = translate_value


def detect_language(query_lang: Optional[str] = None, header_lang: Optional[str] = None) -> str:
    """Determine the response language from query parameter or Accept-Language header.

    Priority: query param > Accept-Language header > default 'en'
    Returns a supported language code, or DEFAULT_LANGUAGE if invalid.
    """
    lang = query_lang or header_lang
    if not lang:
        return DEFAULT_LANGUAGE
    lang = lang.strip().lower()
    # Handle full locale strings like "hi-IN" → "hi"
    if "-" in lang:
        lang = lang.split("-")[0]
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def translate_response(data: Any, lang: str, field_map: Dict[str, str]) -> Any:
    """Recursively translate string values in a response dict based on field_map.

    Args:
        data: The response data (dict, list, or scalar)
        lang: Target language code
        field_map: Mapping of {response_field_name: translation_category}
            e.g. {"tithi": "tithi", "nakshatra": "nakshatra", "weekday": "weekday"}

    Returns:
        Translated copy of the data. If lang is 'en', returns data unchanged.
    """
    if lang == "en":
        return data

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in field_map and isinstance(value, str):
                result[key] = t(lang, field_map[key], value)
            elif isinstance(value, (dict, list)):
                result[key] = translate_response(value, lang, field_map)
            else:
                result[key] = value
        return result

    if isinstance(data, list):
        return [translate_response(item, lang, field_map) for item in data]

    return data


__all__ = [
    "t",
    "detect_language",
    "translate_response",
    "translate_value",
    "get_category_translations",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
]
