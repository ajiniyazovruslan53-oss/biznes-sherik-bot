"""
Unit tests for message utilities: HTML escaping, Markdown conversion,
and HTML-safe message splitting (>4000 characters).
"""

import pytest
from src.utils.formatting import escape_html, markdown_to_telegram_html, split_message


def test_escape_html():
    raw = '<script>alert("test & win")</script>'
    escaped = escape_html(raw)
    assert "&lt;script&gt;" in escaped
    assert "&amp;" in escaped
    assert "<script>" not in escaped


def test_markdown_to_telegram_html_basic():
    md = "**Qalaysiz** _sherik_! [Reels](test)"
    res = markdown_to_telegram_html(md)
    assert "<b>Qalaysiz</b>" in res
    assert "<i>sherik</i>" in res


def test_markdown_to_telegram_html_headers_and_bullets():
    md = "### Baslı maqset\n* Birinshi qádem\n* Ekinshi qádem"
    res = markdown_to_telegram_html(md)
    assert "<b>Baslı maqset</b>" in res
    assert "• Birinshi qádem" in res
    assert "• Ekinshi qádem" in res


def test_markdown_to_telegram_html_code_blocks():
    md = "Tómendegi kod:\n```python\nprint('salem')\n```\nhám inline `calc_margin` quralı."
    res = markdown_to_telegram_html(md)
    assert '<pre><code class="language-python">' in res
    assert "print('salem')" in res
    assert "<code>calc_margin</code>" in res


def test_split_message_under_limit():
    short_text = "Bul qısqa xabar."
    chunks = split_message(short_text, max_length=4000)
    assert len(chunks) == 1
    assert chunks[0] == short_text


def test_split_message_over_limit_preserves_content():
    # Generate 100 lines of text exceeding 4000 chars
    lines = [f"Qatar {i}: Biznes Sherik studentler ushın jeke AI járdemshi bolıp xızmet etedi." for i in range(120)]
    long_text = "\n\n".join(lines)
    assert len(long_text) > 5000

    chunks = split_message(long_text, max_length=4000)
    assert len(chunks) > 1

    # Every chunk should be <= 4000 chars
    for chunk in chunks:
        assert len(chunk) <= 4000

    # Total characters when rejoined should cover original content
    rejoined = " ".join(chunks)
    assert "Qatar 0:" in rejoined
    assert "Qatar 119:" in rejoined


def test_split_message_balances_open_html_tags():
    # Long text enclosed in <b> ... </b>
    inner = "A" * 3995 + " " + "B" * 100
    long_html = f"<b>{inner}</b>"
    chunks = split_message(long_html, max_length=4000)

    assert len(chunks) == 2
    # First chunk should have closing </b> tag
    assert chunks[0].startswith("<b>")
    assert chunks[0].endswith("</b>")

    # Second chunk should reopen <b> tag
    assert chunks[1].startswith("<b>")
    assert chunks[1].endswith("</b>")
