"""Markdown to Telegram HTML converter."""

import re


def md_to_telegram_html(text: str) -> str:
    """Convert Markdown text to Telegram-safe HTML."""
    if not text:
        return ""

    code_blocks = []

    def save_code_block(match):
        lang = match.group(1) or ""
        code = match.group(2)
        code = _escape_html(code)
        code_blocks.append(f"<pre>{code}</pre>")
        return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

    text = re.sub(r"```(\w*)\n?(.*?)```", save_code_block, text, flags=re.DOTALL)

    inline_codes = []

    def save_inline_code(match):
        code = _escape_html(match.group(1))
        inline_codes.append(f"<code>{code}</code>")
        return f"\x00INLINE{len(inline_codes) - 1}\x00"

    text = re.sub(r"`([^`\n]+)`", save_inline_code, text)

    text = _escape_html(text)

    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)

    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    for i, block in enumerate(code_blocks):
        text = text.replace(f"\x00CODEBLOCK{i}\x00", block)
    for i, code in enumerate(inline_codes):
        text = text.replace(f"\x00INLINE{i}\x00", code)

    text = re.sub(r"^#{1,6}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    text = re.sub(r"^>\s?(.+)$", r"<blockquote>\1</blockquote>", text, flags=re.MULTILINE)

    return text.strip()


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def split_message(text: str, max_len: int = 4000) -> list[str]:
    """Split long messages for Telegram (limit 4096 chars)."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, max_len)
        if split_at < max_len // 2:
            split_at = max_len
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks