#!/bin/bash

# OpenRouterBot Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/a-prs/OpenRouterBot/main/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh

INSTALL_DIR="/opt/openrouterbot"
REPO_URL="https://github.com/a-prs/OpenRouterBot.git"
SERVICE_NAME="openrouterbot"
NODE_MIN_VERSION=18

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}[+]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
fail()  { echo -e "${RED}[x]${NC} $1"; exit 1; }

if [ ! -t 0 ]; then
    echo ""
    echo "  Run this instead:"
    echo ""
    echo "    curl -fsSL https://raw.githubusercontent.com/a-prs/OpenRouterBot/main/install.sh -o /tmp/install.sh && sudo bash /tmp/install.sh"
    echo ""
    exit 1
fi

set -eo pipefail

echo ""
echo -e "${BOLD}======================================${NC}"
echo -e "${BOLD}    OpenRouterBot Installer${NC}"
echo -e "${BOLD}    AI Assistant via Telegram${NC}"
echo -e "${BOLD}    Powered by OpenRouter${NC}"
echo -e "${BOLD}======================================${NC}"
echo ""

if [[ "$1" == "--upgrade" ]]; then
    info "Upgrading OpenRouterBot..."
    cd "$INSTALL_DIR" && git pull
    "$INSTALL_DIR/.venv/bin/pip" install -q -r "$INSTALL_DIR/bot/requirements.txt"
    systemctl restart "$SERVICE_NAME"
    info "Done! Check: systemctl status $SERVICE_NAME"
    exit 0
fi

if [[ $EUID -ne 0 ]]; then
    fail "Run as root: sudo bash $0"
fi

if ! grep -qiE "ubuntu|debian" /etc/os-release 2>/dev/null; then
    warn "This script is designed for Ubuntu/Debian. Proceeding anyway..."
fi

if [[ -d "$INSTALL_DIR/bot" ]]; then
    warn "OpenRouterBot is already installed at $INSTALL_DIR"
    read -p "  Reinstall? (y/N): " reinstall
    if [[ "$reinstall" != "y" && "$reinstall" != "Y" ]]; then
        echo ""
        info "To update: cd $INSTALL_DIR && git pull && systemctl restart $SERVICE_NAME"
        exit 0
    fi
    systemctl stop "$SERVICE_NAME" 2>/dev/null || true
fi

info "Installing system packages..."
apt-get update -qq || fail "apt-get update failed"
apt-get install -y python3 python3-venv python3-pip git curl 2>&1 | tail -3
info "System packages installed"

info "Creating user 'openrouterbot'..."
if id -u openrouterbot &>/dev/null; then
    info "User 'openrouterbot' exists"
else
    useradd -r -d "$INSTALL_DIR" -s /bin/bash openrouterbot
fi

info "Downloading OpenRouterBot..."
if [[ -d "$INSTALL_DIR/.git" ]]; then
    git config --global --add safe.directory "$INSTALL_DIR" 2>/dev/null
    cd "$INSTALL_DIR" && git pull
    info "Repository updated"
else
    if [[ -d "$INSTALL_DIR" ]]; then
        [[ -f "$INSTALL_DIR/.env" ]] && cp "$INSTALL_DIR/.env" /tmp/_openrouterbot_env_backup
        rm -rf "$INSTALL_DIR"
    fi

    git clone "$REPO_URL" "$INSTALL_DIR" || fail "Failed to clone: $REPO_URL"

    [[ -f /tmp/_openrouterbot_env_backup ]] && mv /tmp/_openrouterbot_env_backup "$INSTALL_DIR/.env"
    info "Repository cloned"
fi

info "Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/.venv" || fail "Failed to create venv"

info "Installing Python dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip 2>&1 | tail -1
"$INSTALL_DIR/.venv/bin/pip" install -q -r "$INSTALL_DIR/bot/requirements.txt" 2>&1 | tail -3
info "Python environment ready"

mkdir -p "$INSTALL_DIR/workspace"
mkdir -p "$INSTALL_DIR/data"

if [[ -f "$INSTALL_DIR/.env" ]]; then
    info "Config .env already exists, keeping it"
else
    echo ""
    echo -e "${BOLD}======================================${NC}"
    echo -e "${BOLD}    Configuration${NC}"
    echo -e "${BOLD}======================================${NC}"
    echo ""

    echo "  Step 1: Telegram Bot Token"
    echo "  Get it from @BotFather in Telegram"
    echo ""
    while true; do
        read -p "  Bot token: " BOT_TOKEN
        if [[ "$BOT_TOKEN" =~ ^[0-9]+:.+$ ]]; then
            break
        fi
        warn "  Invalid format. Should look like: 123456:ABC-DEF..."
    done

    echo ""

    echo "  Step 2: Your Telegram Chat ID"
    echo "  Get it from @userinfobot in Telegram"
    echo ""
    while true; do
        read -p "  Chat ID: " CHAT_ID
        if [[ "$CHAT_ID" =~ ^[0-9]+$ ]]; then
            break
        fi
        warn "  Should be a number like: 987654321"
    done

    echo ""

    echo "  Step 3: OpenRouter API Key"
    echo "  Get free key: https://openrouter.ai/keys"
    echo ""
    while true; do
        read -p "  OpenRouter API key: " OR_KEY
        if [[ "$OR_KEY" =~ ^sk-or-v1- ]]; then
            break
        fi
        warn "  Should start with: sk-or-v1-"
    done

    cat > "$INSTALL_DIR/.env" << ENVEOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID
OPENROUTER_API_KEY=$OR_KEY
OPENROUTER_MODEL=qwen/qwen-2.5-72b-instruct
ENVEOF

    chmod 600 "$INSTALL_DIR/.env"
    info "Config saved to $INSTALL_DIR/.env"
fi

chown -R openrouterbot:openrouterbot "$INSTALL_DIR"

echo "openrouterbot ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/openrouterbot
chmod 440 /etc/sudoers.d/openrouterbot
info "Permissions configured"

info "Setting up systemd service..."

cat > /etc/systemd/system/openrouterbot.service << SERVICEEOF
[Unit]
Description=OpenRouterBot
After=network.target

[Service]
Type=simple
User=openrouterbot
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$INSTALL_DIR/.venv/bin/python -m bot.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME" -q
systemctl start "$SERVICE_NAME"

sleep 3

echo ""
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${BOLD}======================================${NC}"
    echo -e "    ${GREEN}OpenRouterBot is running!${NC}"
    echo -e "${BOLD}======================================${NC}"
    echo ""
    echo "  Send a message to your bot in Telegram."
    echo ""
    echo "  Commands:"
    echo "    systemctl status $SERVICE_NAME"
    echo "    journalctl -u $SERVICE_NAME -f"
    echo "    systemctl restart $SERVICE_NAME"
    echo ""
    echo "  Update from Telegram: /update"
    echo ""
else
    warn "Service failed to start. Check logs:"
    echo ""
    journalctl -u "$SERVICE_NAME" --no-pager -n 15
    echo ""
    echo "  Fix the issue and run: systemctl start $SERVICE_NAME"
fi