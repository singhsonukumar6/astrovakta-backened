"""
AI interpretation Celery tasks.
"""
import json
import logging
import httpx
from ..celery_app import celery_app
from ..auth import update_job_status, get_job, store_job_result, get_active_ai_provider
from ..crypto import decrypt_api_key

logger = logging.getLogger(__name__)

PROVIDER_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "together": "https://api.together.xyz/v1/chat/completions",
}

PROVIDER_HEADERS = {
    "openai": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    "anthropic": lambda key: {"x-api-key": key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
    "groq": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    "together": lambda key: {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
}


def _build_ai_context(input_data: dict) -> str:
    """Build a rich context string from birth chart data for AI prompt."""
    parts = []
    parts.append(f"Birth: {input_data.get('dateOfBirth')} at {input_data.get('timeOfBirth')}")
    parts.append(f"Location: {input_data.get('latitude')}, {input_data.get('longitude')}")
    parts.append(f"Timezone: {input_data.get('timezone')}")

    if "planets" in input_data:
        parts.append("\nPlanets:")
        for p in input_data["planets"]:
            retro = " (R)" if p.get("isRetrograde") else ""
            parts.append(f"  {p['name']}: {p.get('sign','')} {p.get('degree',''):.1f}° House {p.get('house','?')} {p.get('houseStatus','')}{retro}")

    if "houses" in input_data:
        parts.append("\nHouses:")
        for h in input_data["houses"]:
            parts.append(f"  House {h.get('number','')}: {h.get('sign','')} Lord {h.get('signLord','')} Planets: {', '.join(h.get('planets', [])) or 'empty'}")

    if "yogas" in input_data and input_data["yogas"]:
        parts.append("\nYogas: " + ", ".join(y.get("name", "") for y in input_data["yogas"][:10]))

    if "doshas" in input_data and input_data["doshas"]:
        active = [d for d in input_data["doshas"] if d.get("present")]
        if active:
            parts.append("\nActive Doshas: " + ", ".join(d.get("name", "") for d in active))

    return "\n".join(parts)


@celery_app.task(name="app.workers.ai_worker.ai_chat", bind=True, max_retries=2)
def ai_chat_task(self, job_id: int):
    """Process an AI chat request using the user's configured AI provider."""
    try:
        job = get_job(job_id)
        if not job:
            return

        update_job_status(job_id, "processing")
        input_data = json.loads(job["input_data"])
        user_id = job["user_id"]

        provider_config = get_active_ai_provider(user_id)
        if not provider_config:
            update_job_status(job_id, "failed",
                              error_message="No AI provider configured. Add one in Dashboard → AI Providers.")
            return

        api_key = decrypt_api_key(provider_config["api_key_encrypted"])
        provider = provider_config["provider"]
        model = provider_config.get("model") or _default_model(provider)

        chart_context = _build_ai_context(input_data)
        question = input_data.get("question", "Provide a general life reading based on this birth chart.")

        system_prompt = (
            "You are an expert Vedic astrologer. Provide detailed, insightful readings based on the "
            "birth chart data provided. Be specific, mention planetary positions, houses, and nakshatras. "
            "Provide practical remedies when relevant. Use clear, accessible language."
        )
        user_prompt = f"Birth Chart Data:\n{chart_context}\n\nQuestion: {question}"

        response_text = _call_ai_api(provider, api_key, model, system_prompt, user_prompt)

        result = {
            "answer": response_text,
            "provider": provider,
            "model": model,
            "topic": _detect_topic(question),
        }
        store_job_result(job_id, "json", json.dumps(result).encode())
        update_job_status(job_id, "completed", result_data=json.dumps(result))

    except Exception as e:
        logger.exception(f"AI chat job {job_id} failed")
        update_job_status(job_id, "failed", error_message=str(e))


@celery_app.task(name="app.workers.ai_worker.ai_interpretation", bind=True, max_retries=2)
def ai_interpretation_task(self, job_id: int):
    """Generate a full kundli interpretation using AI."""
    try:
        job = get_job(job_id)
        if not job:
            return

        update_job_status(job_id, "processing")
        input_data = json.loads(job["input_data"])
        user_id = job["user_id"]

        provider_config = get_active_ai_provider(user_id)
        if not provider_config:
            update_job_status(job_id, "failed",
                              error_message="No AI provider configured. Add one in Dashboard → AI Providers.")
            return

        api_key = decrypt_api_key(provider_config["api_key_encrypted"])
        provider = provider_config["provider"]
        model = provider_config.get("model") or _default_model(provider)

        chart_context = _build_ai_context(input_data)

        system_prompt = (
            "You are a master Vedic astrologer providing a comprehensive birth chart interpretation. "
            "Cover: Personality, Career, Wealth, Health, Relationships, Spirituality, and Predictions. "
            "Be thorough, reference specific planetary positions, house placements, nakshatras, and yogas. "
            "Provide timing of events based on dasha periods. Include practical remedies."
        )
        user_prompt = (
            f"Provide a complete life interpretation for this birth chart:\n\n{chart_context}\n\n"
            "Cover all life areas with detailed analysis."
        )

        response_text = _call_ai_api(provider, api_key, model, system_prompt, user_prompt)

        result = {
            "interpretation": response_text,
            "provider": provider,
            "model": model,
        }
        store_job_result(job_id, "json", json.dumps(result).encode())
        update_job_status(job_id, "completed", result_data=json.dumps(result))

    except Exception as e:
        logger.exception(f"AI interpretation job {job_id} failed")
        update_job_status(job_id, "failed", error_message=str(e))


def _call_ai_api(provider: str, api_key: str, model: str,
                 system_prompt: str, user_prompt: str) -> str:
    """Make the actual API call to the AI provider."""
    endpoint = PROVIDER_ENDPOINTS.get(provider)
    headers_factory = PROVIDER_HEADERS.get(provider)
    if not endpoint or not headers_factory:
        raise ValueError(f"Unsupported provider: {provider}")

    headers = headers_factory(api_key)

    if provider == "anthropic":
        payload = {
            "model": model,
            "max_tokens": 4096,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }
    else:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 4096,
            "temperature": 0.7,
        }

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(endpoint, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

    if provider == "anthropic":
        return data["content"][0]["text"]
    else:
        return data["choices"][0]["message"]["content"]


def _default_model(provider: str) -> str:
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-haiku-20240307",
        "groq": "llama-3.3-70b-versatile",
        "together": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    }
    return defaults.get(provider, "gpt-4o-mini")


def _detect_topic(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ["marriage", "spouse", "love", "partner"]): return "marriage"
    if any(k in q for k in ["career", "job", "work", "profession"]): return "career"
    if any(k in q for k in ["health", "disease", "illness"]): return "health"
    if any(k in q for k in ["wealth", "money", "finance"]): return "wealth"
    if any(k in q for k in ["education", "study", "knowledge"]): return "education"
    return "general"
