"""Internationalization (i18n) support for AstroVakta API.

Usage:
    from app.i18n import t, detect_language

    # In endpoint handler:
    lang = detect_language(query_lang=body.lang, header_lang=accept_lang)
    response_data["tithi"] = t("tithi", raw_tithi, lang)
"""
import asyncio
import logging
from typing import Optional, Dict, Any, Union, List
from .languages import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from .registry import translate_value, get_category_translations
from .ai_translate import translate_texts

logger = logging.getLogger(__name__)

# Alias for convenience
t = translate_value


def detect_language(query_lang: Optional[str] = None, header_lang: Optional[str] = None) -> str:
    """Determine the response language from query parameter or Accept-Language header.

    Priority: query param > Accept-Language header > default 'en'
    Returns a supported language code, or DEFAULT_LANGUAGE if invalid.

    Note: Pydantic defaults `lang` fields to "en", so we treat "en" as
    unset to allow Accept-Language header fallback to work correctly.
    """
    # Treat None, empty, or the Pydantic default "en" as unset
    effective_query = query_lang if query_lang and query_lang.strip().lower() not in ("", "en") else None
    lang = effective_query or header_lang
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


def _get_ai_credentials(request=None):
    """Get AI provider credentials from the request's API key info.

    Returns (api_key, provider, model) or (None, None, None) if unavailable.
    """
    if not request:
        return None, None, None

    try:
        key_info = getattr(getattr(request, 'state', None), 'api_key_info', None)
        user_id = key_info.get('user_id') if key_info else None
        if not user_id:
            logger.warning("i18n: No user_id in request state — skipping AI translation")
            return None, None, None

        from ..auth import get_active_ai_provider
        from ..crypto import decrypt_api_key

        provider_config = get_active_ai_provider(user_id)
        if not provider_config:
            logger.warning("i18n: No active AI provider for user %s", user_id)
            return None, None, None

        api_key = decrypt_api_key(provider_config["api_key_encrypted"])
        provider = provider_config["provider"]
        _DEPRECATED_MODELS = {
            "groq": {
                "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
                "llama-3.1-8b-instant": "openai/gpt-oss-120b",
                "mixtral-8x7b-32768": "openai/gpt-oss-120b",
            },
        }
        saved_model = provider_config.get("model")
        model = saved_model or {
            "openai": "gpt-4o-mini", "anthropic": "claude-3-haiku-20240307",
            "groq": "openai/gpt-oss-120b",
            "together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        }.get(provider, "gpt-4o-mini")
        deprecated = _DEPRECATED_MODELS.get(provider, {})
        if model in deprecated:
            logger.warning("i18n: Model %s is deprecated for %s, using %s instead", model, provider, deprecated[model])
            model = deprecated[model]

        logger.warning("i18n: Using AI provider %s/%s for user %s", provider, model, user_id)
        return api_key, provider, model
    except Exception as e:
        logger.warning("i18n: Could not get AI credentials: %s", e)
        return None, None, None


async def translate_paragraphs(data: Any, lang: str, request=None,
                               min_length: int = 30) -> Any:
    """Translate all long string values in a nested response using AI.

    Recursively walks the response, collects all string values longer than
    min_length, batch-translates them via AI, and writes them back.
    Dictionary-based translation (translate_response) should run FIRST
    to handle short terms; this handles the remaining long free-text.
    """
    if lang == "en":
        return data

    api_key, provider, model = _get_ai_credentials(request)
    if not api_key:
        logger.warning("i18n: translate_paragraphs — no AI credentials, skipping")
        return data

    # Phase 1: collect long strings and their locations
    texts: List[str] = []
    locations: List[tuple] = []

    def _collect(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str) and len(v) >= min_length:
                    texts.append(v)
                    locations.append((obj, k))
                elif isinstance(v, (dict, list)):
                    _collect(v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                if isinstance(v, str) and len(v) >= min_length:
                    texts.append(v)
                    locations.append((obj, i))
                elif isinstance(v, (dict, list)):
                    _collect(v)

    _collect(data)

    if not texts:
        logger.warning("i18n: translate_paragraphs — no long strings found (min_length=%d)", min_length)
        return data

    logger.warning("i18n: translate_paragraphs — translating %d texts via %s/%s", len(texts), provider, model)

    # Phase 2: AI translate in batch (run sync AI call in thread to avoid blocking event loop)
    translated = await asyncio.to_thread(translate_texts, texts, lang, api_key, provider, model)

    if translated == texts:
        logger.warning("i18n: translate_paragraphs — AI returned unchanged texts (translation failed)")

    # Phase 3: write back
    for (parent, key), new_text in zip(locations, translated):
        parent[key] = new_text

    return data


__all__ = [
    "t",
    "detect_language",
    "translate_response",
    "translate_paragraphs",
    "translate_texts",
    "translate_value",
    "get_category_translations",
    "SUPPORTED_LANGUAGES",
    "DEFAULT_LANGUAGE",
]
