"""OpenRouterBot configuration — loaded from .env."""

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-haiku")
OPENROUTER_MAX_TURNS = int(os.getenv("OPENROUTER_MAX_TURNS", "15"))
OPENROUTER_TIMEOUT = int(os.getenv("OPENROUTER_TIMEOUT", "600"))

WORK_DIR = Path(os.getenv("WORK_DIR", str(PROJECT_ROOT / "workspace")))

DB_PATH = PROJECT_ROOT / "data" / "bot.db"

MESSAGE_QUEUE_MAX = 5
SESSION_IDLE_TIMEOUT_HOURS = 48

_openrouter_models = [
    "anthropic/claude-3.5-sonnet",
    "anthropic/claude-3-haiku",
    "qwen/qwen-2.5-72b-instruct",
    "qwen/qwen-2.5-32b-instruct",
    "google/gemini-2.0-flash-exp",
    "meta-llama/llama-3.3-70b-instruct",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
]


def set_env_var(key: str, value: str):
    """Write or update a variable in .env file."""
    lines = []
    found = False

    if ENV_PATH.exists():
        lines = ENV_PATH.read_text().splitlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                found = True
                break

    if not found:
        lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(lines) + "\n")
    os.environ[key] = value


def reload_config():
    """Reload configuration from .env."""
    load_dotenv(ENV_PATH, override=True)


def get_model_list() -> list:
    """Get list of available OpenRouter models."""
    return _openrouter_models