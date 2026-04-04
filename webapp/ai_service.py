"""
AI analysis service for the scraper webapp.
Supports OpenRouter, OpenAI, Anthropic, and custom providers.
"""

from __future__ import annotations
from typing import Optional
import httpx

PROVIDER_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
}


async def call_chat_completion(
    api_key: str,
    model: str,
    messages: list[dict],
    base_url: Optional[str],
    provider: str,
) -> str:
    """
    Call a chat completion endpoint and return the assistant's response text.
    """
    url = (base_url or PROVIDER_BASE_URLS.get(provider, "")).rstrip("/") + "/chat/completions"

    headers: dict[str, str] = {"Content-Type": "application/json"}

    if provider == "anthropic":
        headers["x-api-key"] = api_key
        headers["anthropic-version"] = "2023-06-01"
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    if provider == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/ToDiii/just-testing"
        headers["X-Title"] = "Gemeinde Scraper"

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 2048,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    # Handle Anthropic's response format
    if provider == "anthropic":
        return data["content"][0]["text"]

    # OpenAI / OpenRouter format
    return data["choices"][0]["message"]["content"]


def build_analysis_prompt(
    results: list[dict],
    mode: str,
    system_prompt: Optional[str],
) -> list[dict]:
    """
    Build the messages list for the chat completion API.
    """
    from .schemas import DEFAULT_SYSTEM_PROMPT

    sys = system_prompt or DEFAULT_SYSTEM_PROMPT

    entries = []
    for i, r in enumerate(results, 1):
        entries.append(
            f"{i}. **{r.get('title', 'Kein Titel')}**\n"
            f"   Quelle: {r.get('source', '—')} | Datum: {r.get('publication_date', '—')}\n"
            f"   URL: {r.get('url', '—')}\n"
            f"   {r.get('description', '')[:200]}"
        )

    body = "\n\n".join(entries)

    mode_instruction = (
        "Erstelle eine kurze Zusammenfassung der wichtigsten Erkenntnisse."
        if mode == "summary"
        else "Analysiere jeden Eintrag einzeln und gib detaillierte Einschätzungen."
    )

    user_msg = (
        f"Analysiere diese {len(results)} Scraping-Ergebnisse:\n\n"
        f"{body}\n\n"
        f"{mode_instruction}"
    )

    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user_msg},
    ]
