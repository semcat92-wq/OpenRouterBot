"""OpenRouter runner — HTTP API calls with in-memory message queue."""

import asyncio
import logging
from typing import Optional, Callable

import httpx

import config
from db import get_session_history, save_message

logger = logging.getLogger("runner")

_is_busy = False
_message_queue: list[dict] = []


def is_busy() -> bool:
    return _is_busy


def queue_length() -> int:
    return len(_message_queue)


MESSAGE_QUEUE_MAX = 5


class QueueFull(Exception):
    pass


async def run_qwen(
    prompt: str,
    session_id: Optional[str] = None,
    on_result: Optional[Callable] = None,
    max_turns: Optional[int] = None,
    queue_max: int = MESSAGE_QUEUE_MAX,
) -> dict:
    """Send prompt to OpenRouter. If busy, queue the message.

    Returns:
        {"status": "started"} — task launched
        {"status": "queued", "position": N} — added to queue
        {"status": "queue_full"} — rejected
    """
    global _is_busy

    if _is_busy:
        if len(_message_queue) >= queue_max:
            return {"status": "queue_full"}
        _message_queue.append({"text": prompt, "session_id": session_id, "callback": on_result})
        return {"status": "queued", "position": len(_message_queue)}

    _is_busy = True

    asyncio.create_task(_process_prompt(prompt, session_id, on_result))
    return {"status": "started"}


async def _process_prompt(
    prompt: str,
    session_id: Optional[str],
    on_result: Optional[Callable],
):
    """Execute request and drain queue."""
    global _is_busy

    try:
        result = await _execute_openrouter(prompt, session_id)

        new_session_id = result.get("session_id", session_id) if result else session_id
        result_text = result.get("result", "") if result else ""

        if on_result:
            await on_result(result_text, new_session_id)

        while _message_queue:
            queued = _message_queue.pop(0)
            sid = new_session_id or queued.get("session_id")
            combined_prompt = queued["text"]

            qr = await _execute_openrouter(combined_prompt, sid)
            q_text = qr.get("result", "") if qr else ""
            q_sid = qr.get("session_id", sid) if qr else sid
            new_session_id = q_sid

            cb = queued.get("callback")
            if cb:
                await cb(q_text, q_sid)

    except Exception as e:
        logger.error(f"Error in _process_prompt: {e}", exc_info=True)
        if on_result:
            await on_result(f"Error: {e}", session_id)
    finally:
        _is_busy = False


async def _execute_openrouter(
    prompt: str,
    session_id: Optional[str] = None,
) -> Optional[dict]:
    """Call OpenRouter API."""

    if not config.OPENROUTER_API_KEY:
        return {"error": "OpenRouter API key not configured"}

    messages = [{"role": "system", "content": "You are a helpful AI coding assistant. Provide clear, detailed code examples when appropriate."}]

    if session_id:
        history = get_session_history(session_id)
        for msg in history[-10:]:
            messages.append({"role": msg["role"], "content": msg["text"]})

    messages.append({"role": "user", "content": prompt})

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

    try:
        async with httpx.AsyncClient(timeout=config.OPENROUTER_TIMEOUT) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
            )

        if response.status_code != 200:
            error = response.text[:500]
            logger.error(f"OpenRouter API error {response.status_code}: {error}")
            return {"error": error, "session_id": session_id}

        data = response.json()
        result_text = data["choices"][0]["message"]["content"]

        new_session_id = session_id or f"session_{data.get('id', 'new')[:8]}"
        
        save_message("user", prompt, new_session_id)
        save_message("assistant", result_text, new_session_id)

        return {"result": result_text, "session_id": new_session_id}

    except httpx.TimeoutException:
        logger.error(f"OpenRouter timeout after {config.OPENROUTER_TIMEOUT}s")
        return {"error": "timeout", "session_id": session_id}
    except Exception as e:
        logger.error(f"OpenRouter error: {e}", exc_info=True)
        return {"error": str(e), "session_id": session_id}