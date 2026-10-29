"""
Formatting utilities for Telegram HTML messages.
Includes HTML escaping, markdown conversion, and safe splitting of messages >4000 chars.
"""

import html
import re
from typing import List


def escape_html(text: str) -> str:
    """Escapes HTML special characters for safe use in Telegram HTML mode."""
    if not text:
        return ""
    return html.escape(text, quote=False)


def markdown_to_telegram_html(text: str) -> str:
    """
    Converts standard Markdown (commonly output by Gemini) into valid Telegram HTML.
    Handles:
    - Code blocks (```lang ... ```) -> <pre><code class="language-...">...</code></pre>
    - Inline code (`...`) -> <code>...</code>
    - Headers (### ...) -> <b>...</b>
    - Bullet points (* or -) -> •
    - Bold (**...** or __...__) -> <b>...</b>
    - Italic (*...* or _..._) -> <i>...</i>
    - Escapes unformatted text.
    """
    if not text:
        return ""

    # Placeholder storage for protected code blocks to avoid escaping inside code
    code_blocks = []
    
    def save_code_block(match):
        lang = match.group(1) or ""
        code_content = match.group(2)
        idx = len(code_blocks)
        escaped_code = html.escape(code_content, quote=False)
        if lang:
            replacement = f'<pre><code class="language-{lang}">{escaped_code}</code></pre>'
        else:
            replacement = f'<pre><code>{escaped_code}</code></pre>'
        code_blocks.append(replacement)
        return f"\x02CB_{idx}\x03"

    # 1. Preserve multiline code blocks ```lang\ncode\n```
    text = re.sub(r'```([a-zA-Z0-9_-]*)\n?(.*?)```', save_code_block, text, flags=re.DOTALL)

    # 2. Preserve inline code `code`
    inline_codes = []
    def save_inline_code(match):
        code_content = match.group(1)
        idx = len(inline_codes)
        inline_codes.append(f"<code>{html.escape(code_content, quote=False)}</code>")
        return f"\x02IC_{idx}\x03"

    text = re.sub(r'`([^`]+)`', save_inline_code, text)

    # 3. Escape HTML characters in the rest of the text
    text = html.escape(text, quote=False)

    # 4. Headers: ### Header -> <b>Header</b>
    text = re.sub(r'^(?:#{1,6})\s+(.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)

    # 5. Convert bullet points: "* " or "- " at start of line -> "• " BEFORE italic parsing
    text = re.sub(r'^[*-]\s+', '• ', text, flags=re.MULTILINE)

    # 6. Bold: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

    # 7. Italic: *text* or _text_ (single line)
    text = re.sub(r'(?<!\w)\*([^*\n]+?)\*(?!\w)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!\w)_([^_\n]+?)_(?!\w)', r'<i>\1</i>', text)

    # 8. Restore inline code
    for idx, replacement in enumerate(inline_codes):
        text = text.replace(f"\x02IC_{idx}\x03", replacement)

    # 9. Restore code blocks
    for idx, replacement in enumerate(code_blocks):
        text = text.replace(f"\x02CB_{idx}\x03", replacement)

    return text.strip()


def split_message(text: str, max_length: int = 4000) -> List[str]:
    """
    Safely splits a long message into chunks under `max_length` (Telegram limit is 4096).
    Tries to split at:
    1. Paragraph boundaries (\n\n)
    2. Line breaks (\n)
    3. Sentence endings or spaces
    Keeps opening/closing HTML tags intact or balances them across chunks.
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while len(remaining) > max_length:
        split_idx = -1
        # Try finding double newline
        idx = remaining.rfind("\n\n", 0, max_length)
        if idx != -1 and idx >= max_length // 3:
            split_idx = idx + 2
        else:
            # Try single newline
            idx = remaining.rfind("\n", 0, max_length)
            if idx != -1 and idx >= max_length // 3:
                split_idx = idx + 1
            else:
                # Try space
                idx = remaining.rfind(" ", 0, max_length)
                if idx != -1 and idx >= max_length // 3:
                    split_idx = idx + 1
                else:
                    # Force hard split at max_length
                    split_idx = max_length

        chunk = remaining[:split_idx].strip()
        remaining = remaining[split_idx:].strip()
        if chunk:
            chunks.append(chunk)

    if remaining:
        chunks.append(remaining)

    # Check and balance tags across chunks if any tags were opened and not closed
    balanced_chunks = []
    tag_pattern = re.compile(r'<(/?)(b|i|u|s|code|pre|blockquote)(?:[^>]*)>')

    opened_tags = []
    for chunk in chunks:
        # Prepend tags that were open from previous chunk
        current_chunk = "".join([f"<{t}>" for t in opened_tags]) + chunk
        
        # Scan current chunk to find tags state
        matches = tag_pattern.findall(current_chunk)
        stack = []
        for is_closing, tag_name in matches:
            if not is_closing:
                stack.append(tag_name)
            else:
                if stack and stack[-1] == tag_name:
                    stack.pop()
                elif tag_name in stack:
                    stack.remove(tag_name)

        # Close any leftover open tags at the end of this chunk
        closing_tags = "".join([f"</{t}>" for t in reversed(stack)])
        current_chunk += closing_tags
        balanced_chunks.append(current_chunk)
        opened_tags = stack

    return balanced_chunks
