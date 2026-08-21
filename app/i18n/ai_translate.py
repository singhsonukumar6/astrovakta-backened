"""AI-powered translation for long free-text descriptions.

For text that exceeds dictionary-based translation (e.g., dosha descriptions,
yoga predictions, rudraksha details), this module uses the user's configured
AI provider to translate paragraphs in bulk.
"""
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

LANG_NAMES = {
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
}


def _call_ai(prompt: str, api_key: str, provider: str = "openai",
             model: str = None) -> Optional[str]:
    """Call an AI provider for translation. Returns None on failure."""
    try:
        if provider == "openai":
            import openai
            client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model or "gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            resp = client.messages.create(
                model=model or "claude-sonnet-4-20250514",
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        elif provider == "groq":
            import groq
            client = groq.Groq(api_key=api_key)
            resp = client.chat.completions.create(
                model=model or "llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
        elif provider == "together":
            import openai
            client = openai.OpenAI(api_key=api_key, base_url="https://api.together.xyz/v1")
            resp = client.chat.completions.create(
                model=model or "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("AI translation failed (%s): %s", provider, e)
        return None


def translate_texts(texts: List[str], lang: str, api_key: str,
                    provider: str = "openai", model: str = None) -> List[str]:
    """Translate a list of text strings using AI.

    Returns the original texts if lang is 'en', no api_key, or on failure.
    """
    if lang == "en" or not api_key or not texts:
        return texts

    lang_name = LANG_NAMES.get(lang, lang)
    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(texts))
    prompt = (
        f"Translate these {len(texts)} astrological text(s) to {lang_name}. "
        f"Return ONLY a JSON array of translated strings, in the same order. "
        f"Preserve all technical terms, planetary names, and formatting. "
        f"Do not add explanations.\n\n{numbered}"
    )

    result = _call_ai(prompt, api_key, provider, model)
    if not result:
        return texts

    try:
        import json
        # Strip markdown code fences if present
        cleaned = result.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
        translated = json.loads(cleaned)
        if isinstance(translated, list) and len(translated) == len(texts):
            return translated
    except (json.JSONDecodeError, IndexError):
        pass

    return texts
