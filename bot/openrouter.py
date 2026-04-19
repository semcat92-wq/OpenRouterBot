"""OpenRouter API client — HTTP calls to OpenRouter LLM endpoint."""

import asyncio
import json
import logging
from typing import Optional

import httpx

import config
from db import get_session_history

logger = logging.getLogger("openrouter")

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


async def chat(
    prompt: str,
    session_id: Optional[str] = None,
    on_result: Optional[callable] = None,
) -> dict:
    """Send message to OpenRouter API.

    Returns:
        {"status": "started"} — task launched
        {"status": "queued", "position": N}
        {"status": "queue_full"}
    """
    from qwen_runner import run_qwen, is_busy, queue_length, MESSAGE_QUEUE_MAX

    if is_busy():
        if queue_length() >= MESSAGE_QUEUE_MAX:
            return {"status": "queue_full"}
        run_qwen(prompt, session_id, on_result)
        return {"status": "queued", "position": queue_length()}

    return await _execute(prompt, session_id, on_result)


async def _execute(
    prompt: str,
    session_id: Optional[str],
    on_result: Optional[callable],
) -> dict:
    """Execute OpenRouter API call."""
    global _is_busy

    if not config.OPENROUTER_API_KEY:
        if on_result:
            await on_result("OpenRouter API key not configured", session_id)
        return {"status": "error", "error": "API key not set"}

    _is_busy = True

    try:
        messages = _build_messages(prompt, session_id)

        headers = {
            "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/a-prs/OpenRouterBot",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.OPENROUTER_MODEL,
            "messages": messages,
            "max_tokens": 8192,
        }

        async with httpx.AsyncClient(timeout=config.OPENROUTER_TIMEOUT) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            error = response.text[:500]
            logger.error(f"OpenRouter API error {response.status_code}: {error}")
            if on_result:
                await on_result(f"API error: {response.status_code}", session_id)
            return {"status": "error", "error": error}

        data = response.json()
        result_text = data["choices"][0]["message"]["content"]

        new_session_id = session_id or f"session_{data.get('id', 'new')}"
        if on_result:
            await on_result(result_text, new_session_id)

        return {"status": "ok", "result": result_text, "session_id": new_session_id}

    except httpx.TimeoutException:
        logger.error(f"OpenRouter timeout after {config.OPENROUTER_TIMEOUT}s")
        if on_result:
            await on_result("Timeout", session_id)
        return {"status": "error", "error": "timeout"}

    except Exception as e:
        logger.error(f"OpenRouter error: {e}", exc_info=True)
        if on_result:
            await on_result(f"Error: {e}", session_id)
        return {"status": "error", "error": str(e)}

    finally:
        _is_busy = False


def _build_messages(prompt: str, session_id: Optional[str]) -> list:
    """Build message list with history for context."""
    messages = [{"role": "system", "content": "You are a helpful AI assistant. Provide clear, detailed answers."}]

    if session_id:
        history = get_session_history(session_id)
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["text"]})

    messages.append({"role": "user", "content": prompt})
    return messages


_is_busy = False