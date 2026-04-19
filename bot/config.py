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

FREE_MODELS = {
    "deepseek/deepseek-r1": {"name": "DeepSeek R1", "context": "131K", "desc": "Best for reasoning"},
    "qwen/qwen3-235b-instruct:free": {"name": "Qwen 3 235B", "context": "131K", "desc": "Best general"},
    "qwen/qwen3-coder:free": {"name": "Qwen 3 Coder", "context": "131K", "desc": "Best for coding"},
    "meta-llama/llama-3.3-70b-instruct": {"name": "Llama 3.3 70B", "context": "131K", "desc": "General purpose"},
    "nvidia/Nemotron-3-Super-4b-chat": {"name": "Nemotron 3 Super", "context": "4K", "desc": "Fast & small"},
    "google/gemma-4-26b-a4b-it:free": {"name": "Gemma 4 26B", "context": "262K", "desc": "Google model"},
    "mistral-small-3.1-24b": {"name": "Mistral Small 3.1", "context": "131K", "desc": "Balanced"},
    "openrouter/free": {"name": "Free Router", "context": "200K", "desc": "Auto-select best free"},
}

PAID_MODELS = {
    "anthropic/claude-3.5-sonnet": {"name": "Claude 3.5 Sonnet", "context": "200K", "desc": "Best overall"},
    "anthropic/claude-3-haiku": {"name": "Claude 3 Haiku", "context": "200K", "desc": "Fast"},
    "qwen/qwen-2.5-72b-instruct": {"name": "Qwen 2.5 72B", "context": "32K", "desc": "Coding"},
    "openai/gpt-4o": {"name": "GPT-4o", "context": "128K", "desc": "OpenAI best"},
    "openai/gpt-4o-mini": {"name": "GPT-4o Mini", "context": "64K", "desc": "Fast & cheap"},
}


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


def get_model_list() -> dict:
    """Get dict of available OpenRouter models by category."""
    return {"free": FREE_MODELS, "paid": PAID_MODELS}


def get_all_models() -> list:
    """Get flat list of all model IDs."""
    return list(FREE_MODELS.keys()) + list(PAID_MODELS.keys())