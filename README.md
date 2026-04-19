# OpenRouterBot

Personal AI assistant in Telegram, powered by OpenRouter API.

**Free**: Many models available with free tier (Qwen, Claude 3 Haiku, Gemini Flash, etc.)

## What it does

- Chat with AI through Telegram
- Session management (create, switch, close)
- HTML formatting for code blocks and structured responses
- Auto-start via systemd

## Install (3 steps)

### Prerequisites

- Ubuntu/Debian VPS
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- Your Chat ID from [@userinfobot](https://t.me/userinfobot)
- OpenRouter API key from [openrouter.ai/keys](https://openrouter.ai/keys)

### One-line install

```bash
curl -fsSL https://raw.githubusercontent.com/a-prs/OpenRouterBot/main/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh
```

The installer will:

1.  Install Python and dependencies
2.  Ask for your Telegram bot token, chat ID, and OpenRouter API key
3.  Set up and start the bot

## Usage

Just send a message to your bot in Telegram.

**Commands:**

-   `/menu` — control panel
-   `/new` — start new session
-   `/sessions` — list sessions
-   `/status` — system status
-   `/models` — available models

## Update

```bash
cd /opt/openrouterbot && git pull && systemctl restart openrouterbot
```

## Manage

```bash
systemctl status openrouterbot     # check status
systemctl restart openrouterbot    # restart
journalctl -u openrouterbot -f     # view logs
```

## Configuration

Edit `/opt/openrouterbot/.env`:

Variable | Required | Description
--- | --- | ---
`TELEGRAM_BOT_TOKEN` | yes | Bot token from @BotFather
`TELEGRAM_CHAT_ID` | yes | Your Telegram user ID
`OPENROUTER_API_KEY` | yes | API key from openrouter.ai/keys
`OPENROUTER_MODEL` | no | Model to use (default: qwen/qwen-2.5-72b-instruct)
`OPENROUTER_MAX_TURNS` | no | Max iterations (default: 15)
`OPENROUTER_TIMEOUT` | no | Timeout in seconds (default: 600)

## Available Models

Free tier friendly models:
- `qwen/qwen-2.5-72b-instruct` - Best for coding
- `anthropic/claude-3-haiku` - Fast and smart
- `google/gemini-2.0-flash-exp` - Latest Google model
- `openai/gpt-4o-mini` - OpenAI mini model
- `meta-llama/llama-3.3-70b-instruct` - Meta's best

## Architecture

```
/opt/openrouterbot/
  bot/
    main.py          — Telegram bot (aiogram 3.x)
    qwen_runner.py  — OpenRouter API runner
    config.py       — .env loader
    db.py           — SQLite sessions & history
    formatting.py   — Markdown to Telegram HTML
  workspace/       — Working directory
  data/            — SQLite database
  .env             — configuration
```

## License

MIT