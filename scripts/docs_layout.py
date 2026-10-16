"""Shared HTML building blocks for the docs site (``docs/*.html``).

Styling lives in ``docs/assets/site.css`` and behaviour (theme toggle, menu,
section highlighting, before/after sliders, copy buttons, look switcher and
the examples filter) in ``docs/assets/site.js``; both are plain static files,
so the generated pages need no build tooling.
"""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

REPO_URL = "https://github.com/subwaymatch/layer-is-python"


@dataclass(frozen=True)
class Page:
    filename: str
    label: str  # sidebar label (sentence case)
    title: str  # <h1> and pager label (title case)


PAGES: list[Page] = [
    Page("index.html", "Overview", "Overview"),
    Page("examples.html", "Examples", "Examples"),
    Page("blend-modes.html", "Blend modes", "Blend Modes"),
    Page("operations.html", "Operations", "Operations"),
    Page("api.html", "API reference", "API Reference"),
]

# A sidebar entry for a section of the current page: (anchor id, label, level).
# Level 2 entries are method names, shown indented in a monospace font.
Section = tuple[str, str, int]

# The Layer.is logo (docs/assets/logo.svg), used in the sidebar and as favicon.
LOGO = "assets/logo.svg"

ASSETS_DIR = Path(__file__).resolve().parent.parent / "docs" / "assets"


@cache
def asset_url(name: str) -> str:
    """URL of a file in docs/assets/ with a hash of its contents appended.

    GitHub Pages serves assets under fixed names with a 10-minute cache, so
    without this a browser can pair a freshly built page with a stale
    stylesheet. The hash gives every version of a file its own URL.
    """
    digest = hashlib.sha256((ASSETS_DIR / name).read_bytes()).hexdigest()[:10]
    return f"assets/{name}?v={digest}"

# GitHub's "mark-github" octicon (MIT licensed, github.com/primer/octicons).
GITHUB_ICON = (
    '<svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">'
    '<path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 '
    "0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59"
    "-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09"
    "-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 "
    "3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83"
    "-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 "
    '1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg>'
)

# Theme toggle icons: a moon in the light theme, a sun in the dark one.
THEME_ICONS = (
    '<svg class="icon-moon" viewBox="0 0 20 20" width="17" height="17" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M16.2 12.4A6.6 6.6 0 0 1 7.6 3.8a6.6 6.6 0 1 0 8.6 8.6Z"/></svg>'
    '<svg class="icon-sun" viewBox="0 0 20 20" width="17" height="17" fill="none" '
    'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true">'
    '<circle cx="10" cy="10" r="3.3"/><path d="M10 2.6v1.7M10 15.7v1.7M2.6 10h1.7M15.7 '
    '10h1.7M4.8 4.8L6 6M14 14l1.2 1.2M4.8 15.2L6 14M14 6l1.2-1.2"/></svg>'
)

MENU_ICONS = (
    '<svg class="icon-menu" viewBox="0 0 20 20" width="20" height="20" fill="none" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">'
    '<path d="M3 5.5h14M3 10h14M3 14.5h14"/></svg>'
    '<svg class="icon-close" viewBox="0 0 20 20" width="20" height="20" fill="none" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">'
    '<path d="M5 5l10 10M15 5L5 15"/></svg>'
)

# Schibsted Grotesk for text, Besley for headings and DM Mono for code.
FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,400;0,500;1,400"
    "&family=Schibsted+Grotesk:wght@400;500;600&family=Besley:wght@400;500;600&display=swap"
)

# Runs before first paint so a saved theme does not flash the other one. The
# "js" class reveals controls that only work with site.js (the examples filter).
THEME_SCRIPT = (
    "document.documentElement.classList.add('js');"
    "try{var t=localStorage.getItem('layeris-docs-theme');"
    "if(t==='light'||t==='dark')document.documentElement.dataset.theme=t}catch(e){}"
)


def esc(text: str) -> str:
    return html.escape(text, quote=True)


# ----------------------------------------------------------------------
# Title case for headings ("Rescue a Flat Photo", "Film & Vintage")
# ----------------------------------------------------------------------

_MINOR_WORDS = {
    "a", "an", "the", "and", "or", "but", "nor", "for", "of", "to", "in", "on", "at",
    "by", "with", "as", "from",
}


def _cap_word(word: str) -> str:
    word = re.sub(r"^([(\"']?)([a-z])", lambda m: m.group(1) + m.group(2).upper(), word)
    return re.sub(r"-([a-z])", lambda m: "-" + m.group(1).upper(), word)


def title_case(text: str) -> str:
    return " ".join(
        word.lower() if i > 0 and word.lower() in _MINOR_WORDS else _cap_word(word)
        for i, word in enumerate(text.split(" "))
    )


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


def code_block(code: str, lang: str = "python", title: str = "", cls: str = "") -> str:
    """A code block with a copy button, optionally under a file name."""
    classes = f"code {cls}".strip()
    content = highlight(code) if lang in ("python", "json") else esc(code)
    block = (
        f'<div class="{classes}">'
        '<button class="code__copy" type="button" data-copy>Copy</button>'
        f'<pre><code class="lang-{lang}">{content}</code></pre>'
        "</div>"
    )
    if title:
        return f'<div class="code-file"><span class="code-file__name">{esc(title)}</span>{block}</div>'
    return block


def method_link(href: str, label: str, paren: str = "()") -> str:
    """A method name such as darken() with the parentheses dimmed."""
    paren_html = f'<span class="paren">{esc(paren)}</span>' if paren else ""
    return f'<a href="{esc(href)}">{esc(label)}{paren_html}</a>'


def method_index(links: list[str], label: str, cls: str = "") -> str:
    """A wrapping row of method links, used as a table of contents."""
    classes = f"method-index {cls}".strip()
    return f'<nav class="{classes}" aria-label="{esc(label)}">{"".join(links)}</nav>'


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
    before: str,
    after: str,
    size: tuple[int, int],
    label: str,
    alt: str,
    lazy: bool = True,
    tags: bool = True,
) -> str:
    """Before/after slider: drag (or use the arrow keys) to move the divider."""
    tag_html = (
        '\n  <span class="compare__tag compare__tag--before">Before</span>'
        '\n  <span class="compare__tag compare__tag--after">After</span>'
        if tags else ""
    )
    return f"""<div class="compare" style="--pos: 50%">
  {img(before, alt, size, "compare__before", lazy)}
  <div class="compare__after">{img(after, "", size, "", lazy)}</div>
  <span class="compare__handle" aria-hidden="true"></span>{tag_html}
  <input class="compare__range" type="range" min="0" max="100" step="5" value="50"
         aria-label="Compare {esc(label)} with the original photo">
</div>"""


def _sidebar_nav(filename: str, sections: list[Section]) -> str:
    groups = []
    for page in PAGES:
        current = page.filename == filename
        attrs = ' aria-current="page"' if current else ""
        items = ""
        if current and sections:
            method = ' class="sidenav__method"'
            links = "".join(
                f'<a href="#{esc(anchor)}"{method if level == 2 else ""}>{esc(label)}</a>'
                for anchor, label, level in sections
            )
            items = f'<div class="sidenav__sections">{links}</div>'
        groups.append(
            f'<div class="sidenav__group"><a class="sidenav__page" href="{page.filename}"'
            f"{attrs}>{esc(page.label)}</a>{items}</div>"
        )
    return f'<nav class="sidenav" aria-label="Docs">{"".join(groups)}</nav>'


def _pager(filename: str) -> str:
    index = next(i for i, p in enumerate(PAGES) if p.filename == filename)
    cells = []
    for offset, label, cls in ((-1, "Previous", "pager__prev"), (1, "Next", "pager__next")):
        target = index + offset
        link = ""
        if 0 <= target < len(PAGES):
            page = PAGES[target]
            link = (
                f'<a href="{page.filename}"><span class="pager__label">{label}</span>'
                f'<span class="pager__title">{esc(page.title)}</span></a>'
            )
        cells.append(f'<div class="{cls}">{link}</div>')
    return f'<nav class="pager" aria-label="Pages">{"".join(cells)}</nav>'


def page(
    *,
    filename: str,
    title: str,
    description: str,
    body: str,
    version: str,
    sections: list[Section],
) -> str:
    """Wrap *body* in the site shell: sidebar, mobile header, pager and footer."""
    full_title = f"{title} | Layer.is" if title != "Layer.is" else "Layer.is"
    theme_button = (
        '<button class="icon-button theme-toggle" type="button" data-theme-toggle '
        f'aria-label="Switch to dark theme" title="Switch to dark theme">{THEME_ICONS}</button>'
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="icon" href="{LOGO}" type="image/svg+xml">
<script>{THEME_SCRIPT}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{esc(FONTS_URL)}">
<link rel="stylesheet" href="{asset_url("site.css")}">
<script src="{asset_url("site.js")}" defer></script>
</head>
<body>
<header class="mobilebar">
  <a class="mobilebar__brand" href="index.html" aria-label="layeris {esc(version)}, overview"><img src="{LOGO}" alt="" width="40" height="35"><span class="version">v{esc(version)}</span></a>
  {theme_button}
  <button class="icon-button menu-toggle" type="button" data-menu-toggle aria-controls="sidebar" aria-expanded="false" aria-label="Open menu">{MENU_ICONS}</button>
</header>
<div class="layout">
<aside class="sidebar" id="sidebar">
  <a class="sidebar__logo" href="index.html" aria-label="layeris overview"><img src="{LOGO}" alt="" width="68" height="59"></a>
  {_sidebar_nav(filename, sections)}
  <div class="sidebar__foot">
    <a class="gh-link" href="{REPO_URL}">{GITHUB_ICON}<span>GitHub</span></a>
    <div class="sidebar__meta">{theme_button}<span class="version">v{esc(version)}</span></div>
  </div>
</aside>
<main class="main">
<div class="main__inner">
{body}
{_pager(filename)}
<footer class="footer">
  <div class="footer__meta"><span>layeris {esc(version)}</span><span>MIT License</span><a href="{REPO_URL}">Source on GitHub</a></div>
  <p>Every result image on this site is rendered by layeris itself with
    <code>scripts/build_docs.py</code>. Sample photos were generated with OpenAI's
    <code>gpt-image-2.5</code> model (<code>scripts/generate_photos.py</code>).</p>
</footer>
</div>
</main>
</div>
</body>
</html>
"""
