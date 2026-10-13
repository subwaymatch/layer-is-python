"""Shared HTML building blocks for the docs site (``docs/*.html``).

Styling lives in ``docs/assets/site.css`` and behaviour (before/after
sliders, copy buttons, look switcher) in ``docs/assets/site.js``; both are
plain static files, so the generated pages need no build tooling.
"""

from __future__ import annotations

import html
import re

REPO_URL = "https://github.com/subwaymatch/layer-is-python"

NAV: list[tuple[str, str]] = [
    ("index.html", "Home"),
    ("examples.html", "Examples"),
    ("blend-modes.html", "Blend modes"),
    ("operations.html", "Operations"),
]

# The Layer.is logo (docs/assets/logo.svg), used in the header and as favicon.
LOGO = '<img class="brand__logo" src="assets/logo.svg" alt="" width="32" height="28">'


def esc(text: str) -> str:
    return html.escape(text, quote=True)


# ----------------------------------------------------------------------
# Syntax highlighting: a tiny tokenizer that covers the snippets we show
# ----------------------------------------------------------------------

_TOKEN_RE = re.compile(
    r"(?P<comment>#[^\n]*)"
    r"|(?P<string>\"[^\"\n]*\"|'[^'\n]*')"
    r"|(?P<number>\b\d+(?:\.\d+)?\b)"
    r"|(?P<keyword>\b(?:from|import|for|in|as|with|def|return|None|True|False)\b)"
    r"|(?P<builtin>\b(?:zip|open|print|json|Path)\b)"
    r"|(?P<name>\b(?:LayerImage|np)\b)"
    r"|(?P<call>(?<=\.)[A-Za-z_]\w*(?=\())"
)


def highlight(code: str) -> str:
    """Return HTML for *code* with <span class="tok-*"> around tokens."""
    out: list[str] = []
    pos = 0
    for match in _TOKEN_RE.finditer(code):
        out.append(esc(code[pos:match.start()]))
        out.append(f'<span class="tok-{match.lastgroup}">{esc(match.group())}</span>')
        pos = match.end()
    out.append(esc(code[pos:]))
    return "".join(out)


def code_block(code: str, lang: str = "python", title: str = "") -> str:
    heading = f'<div class="code__title">{esc(title)}</div>' if title else ""
    return (
        f'<div class="code">{heading}'
        '<button class="code__copy" type="button" data-copy>Copy</button>'
        f'<pre><code class="lang-{lang}">{highlight(code)}</code></pre>'
        "</div>"
    )


# ----------------------------------------------------------------------
# Components
# ----------------------------------------------------------------------


def img(src: str, alt: str, size: tuple[int, int], cls: str = "", lazy: bool = True) -> str:
    width, height = size
    attrs = f' class="{cls}"' if cls else ""
    loading = ' loading="lazy" decoding="async"' if lazy else ""
    return (
        f'<img{attrs} src="{esc(src)}" alt="{esc(alt)}" '
        f'width="{width}" height="{height}"{loading}>'
    )


def compare(
    before: str, after: str, size: tuple[int, int], label: str, alt: str, lazy: bool = True
) -> str:
    """Before/after slider: drag (or use the arrow keys) to move the divider."""
    return f"""<div class="compare" style="--pos: 50%">
  {img(before, f"{alt} (before)", size, "compare__before", lazy)}
  <div class="compare__after">{img(after, f"{alt} (after applying {label})", size, "", lazy)}</div>
  <span class="compare__handle" aria-hidden="true"></span>
  <span class="compare__tag compare__tag--before">Before</span>
  <span class="compare__tag compare__tag--after">After</span>
  <input class="compare__range" type="range" min="0" max="100" value="50"
         aria-label="Move the before/after divider for {esc(label)}">
</div>"""


def page(*, filename: str, title: str, description: str, body: str, version: str) -> str:
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{href}"{current if href == filename else ""}>{name}</a>'
        for href, name in NAV
    )
    full_title = f"{title} | Layer.is" if title != "Layer.is" else "Layer.is"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" href="assets/logo.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/site.css">
<script src="assets/site.js" defer></script>
</head>
<body>
<header class="topbar">
  <div class="wrap topbar__inner">
    <a class="brand" href="index.html">{LOGO}<span>Layer.is</span></a>
    <nav class="nav" aria-label="Main">{nav}</nav>
    <a href="{REPO_URL}" class="gh-link">GitHub</a>
  </div>
</header>
<main>
{body}
</main>
<footer class="footer">
  <div class="wrap footer__inner">
    <p>layeris v{esc(version)} | MIT License |
       <a href="{REPO_URL}">Source on GitHub</a></p>
    <p>Every result image on this site is rendered by layeris itself with
       <code>scripts/build_docs.py</code>. Sample photos were generated with
       OpenAI's <code>gpt-image-2.5</code> model (<code>scripts/generate_photos.py</code>).</p>
  </div>
</footer>
</body>
</html>
"""
