#!/usr/bin/env python3
"""Build the GitHub Pages docs site in ``docs/``.

Every result image on the site is rendered here with layeris itself, from the
sample photos in ``docs/photos/``. Recipe snippets are executed verbatim (see
``scripts/docs_examples.py``), so the code on each page is exactly the code
that produced its image. The script writes:

  * ``index.html``: overview (install, quick start, performance)
  * ``examples.html``: photo recipes with before/after sliders
  * ``blend-modes.html``: every blend mode on several photos
  * ``operations.html``: every operation (via ``generate_previews.py``)
  * ``api.html``: API reference (content in ``scripts/docs_api.py``)

plus the images they reference. Styles and scripts live in ``docs/assets/``.
To publish, enable Settings > Pages > Deploy from a branch with the
``/docs`` folder. No build step is needed on GitHub's side.

Usage::

    python scripts/build_docs.py                         # rebuild docs/
    python scripts/build_docs.py --output-dir /tmp/docs  # build elsewhere
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import FunctionType

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from layeris import LayerImage, __version__  # noqa: E402

import docs_api as api  # noqa: E402  (sibling modules in scripts/)
import docs_layout as layout  # noqa: E402
import generate_previews as previews  # noqa: E402
from docs_examples import (  # noqa: E402
    BATCH_PHOTOS,
    BATCH_PRESET,
    BLEND_COLOR,
    BLEND_MODES,
    BLEND_PHOTOS,
    CATEGORIES,
    COLOR_MODE,
    COLOR_PHOTO,
    COLOR_SWATCHES,
    OPACITY_COLOR,
    OPACITY_MODE,
    OPACITY_PHOTO,
    OPACITY_STEPS,
    PHOTOS,
    RECIPES,
    Recipe,
)

DOCS_DIR = REPO_ROOT / "docs"
PHOTOS_DIR = DOCS_DIR / "photos"
DISPLAY_WIDTH = 960  # recipe before/after images
THUMB_WIDTH = 420  # blend-mode explorer thumbnails
JPEG_QUALITY = 80

# The look switcher at the top of the overview page; the first look shown is
# HERO_LOOKS[0], after the unedited "Original".
HERO_PHOTO = "gamcheon-village"
HERO_LOOKS = ["cross-process", "pastel-dream", "channel-swap"]
ARRAY_SNIPPET = """\
h, w, _ = image.get_image_as_array().shape
t = np.linspace(0, 1, h)[:, np.newaxis, np.newaxis]  # 0 at the top, 1 at the bottom
gradient = (1 - t) * np.array([1.0, 0.6, 0.3]) + t    # orange fading to white

image.multiply(gradient)  # white is neutral for multiply"""

# The walkthrough video on the overview page, rendered by the Remotion project
# in video/ (`npm run render` and `npm run poster` write these files).
VIDEO_SRC = "video/layeris.mp4"
VIDEO_POSTER = "video/poster.jpg"

# Thumbnails beside each page in the overview's "In these docs" list.
CONTENTS_EXAMPLES = ["teal-and-orange", "double-exposure", "cyanotype"]
CONTENTS_BLEND_MODES = [
    ("hanbok-portrait", "soft_light"), ("palace-pond", "color_dodge"), ("lotus-lanterns", "overlay"),
]

# Measured on a 12-megapixel JPEG: load, curve, brightness, contrast, overlay,
# save (see the README's Performance section). (label, value, fraction of max)
PERFORMANCE = [
    ("Time", [("8-bit lookup table", "about 0.2 s", 0.2 / 4.1),
              ("float64 on every pixel", "4.1 s", 1.0)]),
    ("Peak memory", [("8-bit lookup table", "under 200 MB", 200 / 1200),
                     ("float64 on every pixel", "about 1.2 GB", 1.0)]),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def method_title(method: str) -> str:
    return method.replace("_", " ").title()


# ----------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------


@contextmanager
def working_directory(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def run_snippet(snippet: str) -> LayerImage:
    """Execute a recipe snippet and return the `image` it leaves behind."""
    namespace = {"LayerImage": LayerImage, "np": np}
    # Snippets load "photos/<name>.jpg", relative to docs/.
    with working_directory(DOCS_DIR):
        exec(snippet, namespace)  # noqa: S102 (trusted, repo-authored code)
    image = namespace.get("image")
    if not isinstance(image, LayerImage):
        raise TypeError("recipe snippets must leave a LayerImage in `image`")
    return image


def load_photo(slug: str) -> LayerImage:
    return LayerImage.from_file(PHOTOS_DIR / f"{slug}.jpg")


class ImageWriter:
    """Saves display-sized JPEGs and remembers their pixel sizes for <img>."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.sizes: dict[str, tuple[int, int]] = {}

    def save(self, image: LayerImage, rel_path: str, width: int) -> None:
        pil = previews.to_pil(image)
        if pil.width != width:
            height = round(pil.height * width / pil.width)
            pil = pil.resize((width, height), Image.Resampling.LANCZOS)
        path = self.output_dir / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        pil.save(path, quality=JPEG_QUALITY, optimize=True, progressive=True)
        self.sizes[rel_path] = pil.size

    def img(self, rel_path: str, alt: str, cls: str = "", lazy: bool = True) -> str:
        return layout.img(rel_path, alt, self.sizes[rel_path], cls, lazy)


def original_path(photo: str) -> str:
    return f"examples/originals/{photo}.jpg"


def mode_path(photo: str, method: str) -> str:
    return f"blend-modes/{photo}-{method}.jpg"


def opacity_path(opacity: float) -> str:
    return f"blend-modes/opacity-{round(opacity * 100)}.jpg"


def color_path(color: str) -> str:
    return f"blend-modes/color-{color.lstrip('#')}.jpg"


def render_examples(writer: ImageWriter) -> None:
    for photo in PHOTOS:
        writer.save(load_photo(photo), original_path(photo), DISPLAY_WIDTH)
    for recipe in RECIPES:
        writer.save(run_snippet(recipe.snippet), f"examples/{recipe.slug}.jpg", DISPLAY_WIDTH)
    for photo in BATCH_PHOTOS:
        result = load_photo(photo).apply_from_dict(BATCH_PRESET)
        writer.save(result, f"examples/batch/{photo}.jpg", DISPLAY_WIDTH)
    print(f"  rendered {len(PHOTOS)} originals, {len(RECIPES)} recipes, "
          f"{len(BATCH_PHOTOS)} batch results")


def render_blend_modes(writer: ImageWriter) -> None:
    def thumb(slug: str) -> LayerImage:
        image = load_photo(slug)
        height, width = image.get_image_as_array().shape[:2]
        return image.resize(THUMB_WIDTH, round(height * THUMB_WIDTH / width))

    for photo in BLEND_PHOTOS:
        base = thumb(photo)
        writer.save(base, f"blend-modes/{photo}.jpg", THUMB_WIDTH)
        for method, _, _ in BLEND_MODES:
            result = getattr(base.clone(), method)(BLEND_COLOR)
            writer.save(result, mode_path(photo, method), THUMB_WIDTH)

    base = thumb(OPACITY_PHOTO)
    for opacity in OPACITY_STEPS:
        result = getattr(base.clone(), OPACITY_MODE)(OPACITY_COLOR, opacity=opacity)
        writer.save(result, opacity_path(opacity), THUMB_WIDTH)

    base = thumb(COLOR_PHOTO)
    for color in COLOR_SWATCHES:
        result = getattr(base.clone(), COLOR_MODE)(color)
        writer.save(result, color_path(color), THUMB_WIDTH)
    print(f"  rendered {len(BLEND_PHOTOS) * (len(BLEND_MODES) + 1)} blend-mode thumbnails")




# ----------------------------------------------------------------------
# Page helpers
# ----------------------------------------------------------------------

_BLEND_METHODS = [method for method, _, _ in BLEND_MODES]
_OPERATION_SLUGS = {op.slug for op in previews.OPERATIONS}
esc = layout.esc
code = layout.code_block


def page_head(title: str, lede: str) -> str:
    return f"""<header class="intro">
  <h1>{esc(title)}</h1>
  <p class="intro__lede">{lede}</p>
</header>"""


def section_head(title: str, intro: str = "") -> str:
    intro_html = f'\n    <p class="section__intro">{intro}</p>' if intro else ""
    return f"<h2>{esc(title)}</h2>{intro_html}"


@dataclass(frozen=True)
class Use:
    """A layeris method (or NumPy) that a recipe uses, for the examples filter."""

    key: str
    label: str
    paren: str
    reference: str  # where the filter summary links to
    reference_label: str


def recipe_uses(snippet: str) -> list[Use]:
    uses: list[Use] = []
    for method in dict.fromkeys(re.findall(r"\.([a-z_]+)\(", snippet)):
        if method in _BLEND_METHODS:
            reference = f"blend-modes.html#{method}"
        elif method == "curve" or method in _OPERATION_SLUGS:
            reference = f"api.html#{method}"
        else:
            continue
        uses.append(Use(method, method, "()", reference, f"{method}() reference"))
    if "np." in snippet:
        uses.append(Use("numpy", "NumPy", "", "blend-modes.html#arrays", "Blending with arrays"))
    return uses


def recipe_by_slug(slug: str) -> Recipe:
    return next(r for r in RECIPES if r.slug == slug)


def api_method_links() -> list[str]:
    return [layout.method_link(f"api.html#{e.name}", e.name)
            for group in api.GROUPS for e in group.entries]


def blend_mode_links(prefix: str = "") -> list[str]:
    return [layout.method_link(f"{prefix}#{method}", method) for method in _BLEND_METHODS]


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------


def render_index(writer: ImageWriter, preview_size: tuple[int, int]) -> str:
    alt = PHOTOS[HERO_PHOTO].alt
    looks = [("original", "Original", original_path(HERO_PHOTO),
              f'image = LayerImage.from_file("photos/{HERO_PHOTO}.jpg")',
              f"The unedited sample photo, {HERO_PHOTO}.jpg.")]
    looks += [
        (r.slug, r.title, f"examples/{r.slug}.jpg", r.snippet,
         f'From the examples: <a href="examples.html#{r.slug}">{esc(r.title)}</a>')
        for r in map(recipe_by_slug, HERO_LOOKS)
    ]
    selected = 1  # open on the first edited look, not the original
    tabs = "".join(
        f'<button type="button" class="looks__tab" data-look="{key}" '
        f'aria-pressed="{"true" if i == selected else "false"}">{esc(title)}</button>'
        for i, (key, title, _, _, _) in enumerate(looks)
    )
    panels = "".join(
        f'<div class="looks__panel" data-look="{key}"{"" if i == selected else " hidden"}>'
        f'{code(snippet, cls="code--tall")}<p class="looks__note">{note}</p></div>'
        for i, (key, _, _, snippet, note) in enumerate(looks)
    )
    stage = "".join(
        writer.img(src, f"{alt} ({title})", "", lazy=False).replace(
            "<img ", f'<img data-look="{key}"{"" if i == selected else " hidden"} ', 1
        )
        for i, (key, title, src, _, _) in enumerate(looks)
    )

    quickstart = """from layeris import LayerImage

image = LayerImage.from_file("photo.jpg")
(image.grayscale()
      .brightness(0.1)
      .multiply("#3fe28f", opacity=0.7)
      .curve("rgb", [0, 0.1, 0.4, 0.65, 0.9, 1])
      .save("result.jpg"))"""
    load = """from layeris import LayerImage

# From a local file
image = LayerImage.from_file('/path/to/image.jpg')

# From a URL
image = LayerImage.from_url('https://example.com/photo.jpg')

# From a NumPy array (float, values in [0, 1], shape HxWx3 or HxWx4)
import numpy as np
data = np.random.random((100, 100, 3))
image = LayerImage.from_array(data)"""
    save = """# Default quality is 95 for JPEG
image.save('output.jpg')

# Specify JPEG quality (0 to 100)
image.save('output.jpg', quality=85)

# Save as PNG (lossless)
image.save('output.png')"""
    from_source = f"""git clone {layout.REPO_URL}.git
cd layer-is-python
pip install -e ."""

    def bar(label: str, value: str, fraction: float) -> str:
        fill = "perf__fill perf__fill--slow" if fraction == 1 else "perf__fill"
        return (
            f'<div class="perf__bar"><div class="perf__row"><span>{label}</span>'
            f'<span class="perf__value">{value}</span></div><div class="perf__track">'
            f'<div class="{fill}" style="width: {fraction * 100:.1f}%"></div></div></div>'
        )

    metrics = "".join(
        f'\n      <div class="perf__metric"><span class="perf__name">{name}</span>'
        f'{"".join(bar(*row) for row in rows)}</div>'
        for name, rows in PERFORMANCE
    )

    def thumbs(paths: list[str]) -> str:
        return "".join(writer.img(path, "") for path in paths)

    contents = [
        ("examples.html", "Examples",
         f"{len(RECIPES)} complete looks (fixes, color grades, film, black &amp; white and "
         "creative effects), each with a before/after slider and copy-paste code.",
         f'<a class="doc-row__media" href="examples.html" aria-label="Examples">'
         f'{thumbs([f"examples/{s}.jpg" for s in CONTENTS_EXAMPLES])}</a>'),
        ("blend-modes.html", "Blend Modes",
         f"All {len(BLEND_MODES)} blend modes side by side on three photos, plus how opacity "
         "and the blend color change the result.",
         f'<a class="doc-row__media" href="blend-modes.html" aria-label="Blend modes">'
         f'{thumbs([mode_path(p, m) for p, m in CONTENTS_BLEND_MODES])}</a>'),
        ("operations.html", "Operations",
         "A before/after reference for every LayerImage method, from "
         "<code>grayscale()</code> to <code>pin_light()</code>.",
         '<a class="doc-row__media doc-row__media--single" href="operations.html" '
         f'aria-label="Operations">{layout.img("previews/chaining.jpg", "", preview_size)}</a>'),
        ("api.html", "API Reference",
         "Signatures, parameters and return values for every method, plus the keys each "
         "operation takes in a JSON preset.",
         layout.method_index(api_method_links(), "API reference", "doc-row__methods")),
    ]
    contents_rows = "".join(
        f"""
    <div class="doc-row">
      <div class="doc-row__text">
        <h3><a href="{href}">{title}</a></h3>
        <p>{text}</p>
      </div>
      {media}
    </div>"""
        for href, title, text, media in contents
    )

    body = f"""<header class="intro intro--overview">
  <h1 class="wordmark">layeris</h1>
  <p class="intro__lede">A Python library for Photoshop-style blend modes, brightness,
    contrast, hue, saturation and lightness adjustments, and curves on separate RGB
    channels.</p>
  <p class="intro__sub">It is built on NumPy and Pillow. Every operation returns the image,
    so a whole edit reads as one chained pipeline.</p>
</header>

<div class="looks" data-looks>
  <div class="looks__text">
    <div class="looks__tabs" role="group" aria-label="Pick a look">{tabs}</div>
    {panels}
  </div>
  <div class="looks__stage">{stage}</div>
</div>

<section class="section" id="video">
  <h2>Video</h2>
  <p class="section__intro">A short walkthrough: installing, chaining operations, the blend
    modes, curves and a few looks. Every edit in it is rendered by layeris.</p>
  <figure class="video">
    <video controls playsinline preload="metadata" width="1920" height="1080"
        poster="{VIDEO_POSTER}">
      <source src="{VIDEO_SRC}" type="video/mp4">
      <a href="{VIDEO_SRC}">Download the video</a> (MP4).
    </video>
  </figure>
</section>

<section class="section section--roomy" id="install">
  <h2>Install</h2>
  <div class="cols">
    <div class="col" style="--flex: 1 1 300px">
      <h3>From PyPI</h3>
      {code("pip install layeris", "shell")}
      <p class="col__note">Requires Python 3.10 or higher. The only dependencies are NumPy,
        Pillow and Requests.</p>
    </div>
    <div class="col" style="--flex: 1.3 1 360px">
      <h3>From source</h3>
      {code(from_source, "shell")}
    </div>
  </div>
</section>

<section class="section section--roomy" id="quick-start">
  <h2>Quick Start</h2>
  <div class="cols">
    <div class="col col--prose" style="--flex: 1 1 280px">
      <p>Load an image from a file, a URL or a NumPy array, chain operations, and save.
        Every operation mutates the image in place and returns it, so a whole look reads
        as one pipeline.</p>
      <p class="muted">Use <code>clone()</code> to branch off an independent copy first.</p>
    </div>
    <div class="col" style="--flex: 1.5 1 400px">{code(quickstart)}</div>
  </div>

  <h3 class="subhead" id="load-and-save">Load and Save</h3>
  <div class="cols cols--tight">
    <div class="col" style="--flex: 1.4 1 420px">{code(load)}</div>
    <div class="col" style="--flex: 1 1 300px">{code(save)}</div>
  </div>
</section>

<section class="section" id="performance">
  <h2>Performance</h2>
  <div class="cols cols--wide">
    <div class="col col--prose" style="--flex: 1.3 1 360px">
      <p>Photos loaded with <code>from_file()</code> or <code>from_url()</code> stay as 8-bit
        images while you apply per-channel operations: <code>brightness</code>,
        <code>contrast</code>, <code>lightness</code>, <code>curve</code> and every blend mode
        with a hex color. Each of these only depends on a pixel's own channel value, and an
        8-bit channel has just 256 possible values, so instead of processing every pixel,
        layeris updates a 256-entry lookup table. Pillow applies the table in one pass when
        you call <code>resize()</code> or <code>save()</code>.</p>
      <p class="muted"><code>get_image_as_array()</code>, <code>grayscale()</code>,
        <code>hue()</code>, <code>saturation()</code> and blending with a per-pixel NumPy
        array need float pixels, so they convert the image to float64 once and later
        operations run in float64. Either way, the results are identical to processing every
        pixel in float64.</p>
    </div>
    <figure class="col perf" style="--flex: 1 1 300px">
      <figcaption>A 12-megapixel JPEG: load it, apply a curve, brightness, contrast and an
        overlay, then save.</figcaption>{metrics}
    </figure>
  </div>
</section>

<section class="section" id="contents">
  <h2>In These Docs</h2>
  <div class="doc-rows">{contents_rows}
  </div>
</section>"""
    return layout.page(
        filename="index.html",
        title="Layer.is",
        description="Photoshop-style blend modes, adjustments and curves for Python.",
        body=body,
        version=__version__,
        sections=[
            ("video", "Video", 1), ("install", "Install", 1), ("quick-start", "Quick start", 1),
            ("load-and-save", "Load and save", 1), ("performance", "Performance", 1),
            ("contents", "In these docs", 1),
        ],
    )


def render_examples_page(writer: ImageWriter) -> str:
    uses = {r.slug: recipe_uses(r.snippet) for r in RECIPES}
    counts: dict[str, int] = {}
    by_key: dict[str, Use] = {}
    for recipe_uses_list in uses.values():
        for use in recipe_uses_list:
            counts[use.key] = counts.get(use.key, 0) + 1
            by_key[use.key] = use
    filter_order = sorted(by_key.values(), key=lambda u: (-counts[u.key], u.label.lower()))

    def paren(use: Use) -> str:
        return f'<span class="paren">{use.paren}</span>' if use.paren else ""

    def filter_button(use: Use | None) -> str:
        if use is None:
            return (f'<button type="button" class="filter__btn" data-filter-key="" '
                    f'aria-pressed="true"><span>All</span>'
                    f'<span class="filter__count">{len(RECIPES)}</span></button>')
        return (
            f'<button type="button" class="filter__btn" data-filter-key="{use.key}" '
            f'data-filter-name="{esc(use.label + use.paren)}" '
            f'data-filter-ref="{use.reference}" data-filter-ref-label="{esc(use.reference_label)}" '
            f'aria-pressed="false"><span>{esc(use.label)}{paren(use)}</span>'
            f'<span class="filter__count">{counts[use.key]}</span></button>'
        )

    filters = filter_button(None) + "".join(map(filter_button, filter_order))

    def use_buttons(recipe: Recipe) -> str:
        buttons = "".join(
            f'<button type="button" class="uses__btn" data-filter-key="{u.key}" '
            f'title="Show every example that uses {esc(u.label + u.paren)}">'
            f"{esc(u.label)}{paren(u)}</button>"
            for u in uses[recipe.slug]
        )
        return f'<div class="uses"><span class="uses__label">Uses</span>{buttons}</div>'

    category_links = "".join(
        f'<a href="#{slugify(name)}" data-category-link="{slugify(name)}"><span>{esc(name)}</span>'
        f'<span class="toc__count">{sum(r.category == name for r in RECIPES)}</span></a>'
        for name, _ in CATEGORIES
    )
    category_links += ('<a href="#batch"><span>One preset, many photos</span></a>'
                       '<a href="#sample-photos"><span>Sample photos</span></a>')

    sections = []
    for name, intro in CATEGORIES:
        recipes = [r for r in RECIPES if r.category == name]
        articles = "".join(
            f"""
  <article class="recipe{" recipe--first" if i == 0 else ""}" id="{r.slug}" data-uses="{" ".join(u.key for u in uses[r.slug])}">
    <div class="recipe__media">{layout.compare(
        original_path(r.photo), f"examples/{r.slug}.jpg", writer.sizes[f"examples/{r.slug}.jpg"],
        r.title, PHOTOS[r.photo].alt)}</div>
    <div class="recipe__body">
      <h3><a href="#{r.slug}">{esc(layout.title_case(r.title))}</a></h3>
      <p class="recipe__desc">{esc(r.description)}</p>
      {use_buttons(r)}
      {code(r.snippet)}
    </div>
  </article>"""
            for i, r in enumerate(recipes)
        )
        sections.append(f"""<section class="section section--recipes" id="{slugify(name)}" data-category>
  {section_head(layout.title_case(name), esc(intro))}{articles}
</section>""")

    preset_json = json.dumps(BATCH_PRESET, indent=2)
    # Keep each operation on one line for readability.
    preset_json = re.sub(
        r"\{\s+([^{}]*?)\s+\}",
        lambda m: "{" + re.sub(r"\s*\n\s*", " ", m.group(1)) + "}",
        preset_json,
    )
    preset_json = re.sub(r"\[\s+([^\[\]{}]*?)\s+\]",
                         lambda m: "[" + re.sub(r"\s*\n\s*", " ", m.group(1)) + "]",
                         preset_json)
    batch_code = """import json
from pathlib import Path

from layeris import LayerImage

preset = json.loads(Path("warm-matte.json").read_text())
Path("out").mkdir(exist_ok=True)
for path in Path("photos").glob("*.jpg"):
    LayerImage.from_file(path).apply_from_dict(preset).save(f"out/{path.name}")"""
    batch_items = "".join(
        f"""
    <figure>
      {layout.compare(original_path(photo), f"examples/batch/{photo}.jpg",
                      writer.sizes[f"examples/batch/{photo}.jpg"],
                      f"the warm matte preset on {photo}", PHOTOS[photo].alt, tags=False)}
      <figcaption>{photo}.jpg</figcaption>
    </figure>"""
        for photo in BATCH_PHOTOS
    )
    photo_links = "".join(
        f'\n    <a class="photo-link" href="photos/{slug}.jpg" download>'
        f'{writer.img(original_path(slug), p.alt)}<span>{slug}.jpg</span></a>'
        for slug, p in PHOTOS.items()
    )

    lede = (
        f"{len(RECIPES)} looks built from layeris operations, each applied to a real photo. "
        "Drag the divider to compare. Every snippet below is the exact code that rendered its "
        "image, and it runs as-is: it assumes <code>from layeris import LayerImage</code>, "
        '<code>import numpy as np</code> and the <a href="#sample-photos">sample photos</a> '
        'in a <code>photos/</code> folder. Finish with <code>image.save("result.jpg")</code>.'
    )
    body = f"""{page_head("Examples", lede)}
<nav class="toc" aria-label="Categories">{category_links}</nav>
<div class="filter" id="filter" data-filter>
  <div class="filter__row"><span class="filter__label">Filter by method</span>{filters}</div>
  <p class="filter__summary" hidden><span data-filter-summary></span><a data-filter-ref href="#"></a><button type="button" class="link-button" data-filter-clear>Show all examples</button></p>
</div>

{chr(10).join(sections)}

<section class="section" id="batch">
  {section_head("One Preset, Many Photos",
                "Operations can also be described as data. Save a look as JSON and apply it "
                "to a whole folder with <code>apply_from_dict()</code> (or "
                "<code>apply_from_json()</code>). Here is a warm, matte preset on four "
                "different photos.")}
  <div class="stack">
    {code(preset_json, "json", "warm-matte.json")}
    {code(batch_code, title="batch.py")}
  </div>
  <div class="batch">{batch_items}
  </div>
</section>

<section class="section" id="sample-photos">
  {section_head("Sample Photos",
                "Download the originals (1536 x 1024) to run the snippets yourself. They were "
                "generated for these docs with OpenAI's <code>gpt-image-2.5</code> model; the "
                "prompts are in <code>scripts/generate_photos.py</code>.")}
  <div class="photos">{photo_links}
  </div>
</section>"""
    return layout.page(
        filename="examples.html",
        title="Examples",
        description=f"{len(RECIPES)} photo recipes built with layeris, with before/after sliders.",
        body=body,
        version=__version__,
        sections=[(slugify(name), name, 1) for name, _ in CATEGORIES]
        + [("batch", "One preset, many photos", 1), ("sample-photos", "Sample photos", 1)],
    )


def render_blend_modes_page(writer: ImageWriter) -> str:
    groups: dict[str, list[tuple[str, str]]] = {}
    for method, group, formula in BLEND_MODES:
        groups.setdefault(group, []).append((method, formula))
    group_intros = {
        "Darken": "The result is never lighter than the base. White is neutral.",
        "Lighten": "The result is never darker than the base. Black is neutral.",
        "Contrast": "Darken below mid-gray, lighten above it. 50% gray is neutral for "
                    "most of these modes.",
    }

    swatch = (f'<span class="swatch" style="background: {BLEND_COLOR}"></span>'
              f"<code>{BLEND_COLOR}</code>")
    column_head = "".join(f"<span>{photo}</span>" for photo in BLEND_PHOTOS)
    base_thumbs = "".join(
        f'<figure>{writer.img(f"blend-modes/{photo}.jpg", PHOTOS[photo].alt, lazy=False)}'
        f"<figcaption>{photo}</figcaption></figure>"
        for photo in BLEND_PHOTOS
    )

    def mode_row(method: str, formula: str) -> str:
        thumbs = "".join(
            f'<figure><div class="peek">'
            f'{writer.img(mode_path(photo, method), f"{method_title(method)} with {BLEND_COLOR} on the {photo} photo")}'
            f'{writer.img(f"blend-modes/{photo}.jpg", "", "peek__base")}'
            f'<span class="peek__tag">base</span></div>'
            f"<figcaption>{photo}</figcaption></figure>"
            for photo in BLEND_PHOTOS
        )
        return f"""
    <article class="matrix__row" id="{method}">
      <div class="matrix__label">
        <h3><a href="#{method}">{method_title(method)}</a></h3>
        <code class="matrix__call">image.{method}("{BLEND_COLOR}")</code>
        <span class="matrix__formula">{esc(formula)}</span>
      </div>
      <div class="thumbs">{thumbs}</div>
    </article>"""

    group_sections = []
    for group, modes in groups.items():
        rows = "".join(mode_row(method, formula) for method, formula in modes)
        group_sections.append(f"""  <section class="section matrix__group" id="{slugify(group)}-group">
    {section_head(f"{group} Group", group_intros[group])}{rows}
  </section>""")

    opacity_strip = "".join(
        f"<figure>{writer.img(opacity_path(o), f'{method_title(OPACITY_MODE)} at opacity {o:g}')}"
        f"<figcaption>opacity={o:g}</figcaption></figure>"
        for o in OPACITY_STEPS
    )
    color_strip = "".join(
        f"<figure>{writer.img(color_path(c), f'{method_title(COLOR_MODE)} with {c}')}"
        f'<figcaption><span class="swatch" style="background: {c}"></span>{c}</figcaption></figure>'
        for c in COLOR_SWATCHES
    )

    lede = (
        "A blend mode combines the image (the base, <em>A</em>) with a blend layer "
        "(<em>B</em>). The layer can be a hex color, a NumPy array the same size as the image "
        "(a gradient, a texture, another photo) or anything that broadcasts to it. Every mode "
        f"takes an optional <code>opacity</code> from 0 to 1. Below, all {len(BLEND_MODES)} "
        f"modes blend {swatch} into the same three photos. "
        '<span class="hint-hover">Hover a result to see the base photo.</span>'
        '<span class="hint-touch">Press and hold a result to see the base photo.</span>'
    )
    body = f"""{page_head("Blend Modes", lede)}
{layout.method_index(blend_mode_links(), "Blend modes")}

<div class="matrix">
  <div class="matrix__head" aria-hidden="true"><span></span><div>{column_head}</div></div>
  <section class="matrix__row matrix__row--base" id="base">
    <div class="matrix__label">
      <h3>Base Photos</h3>
      <p>The unedited photos that every blend mode below is applied to.</p>
    </div>
    <div class="thumbs">{base_thumbs}</div>
  </section>
{chr(10).join(group_sections)}
</div>

<section class="section" id="opacity">
  {section_head("Opacity",
                "Opacity mixes the blended result back with the original: "
                f'<code>{OPACITY_MODE}("{OPACITY_COLOR}", opacity=...)</code> on the '
                f"{OPACITY_PHOTO} photo.")}
  <div class="strip strip--opacity">{opacity_strip}</div>
</section>

<section class="section" id="colors">
  {section_head("Choosing a Blend Color",
                "The same mode gives very different moods depending on the color: "
                f"<code>{COLOR_MODE}(color)</code> on the {COLOR_PHOTO} photo.")}
  <div class="strip strip--colors">{color_strip}</div>
</section>

<section class="section" id="arrays">
  {section_head("Blending with Arrays",
                "Pass a NumPy array instead of a hex string to blend per pixel. The "
                '<a href="examples.html#creative-effects">creative effects</a> examples use '
                'this for a <a href="examples.html#lomo">vignette</a>, a '
                '<a href="examples.html#graduated-filter">graduated filter</a> and a '
                '<a href="examples.html#double-exposure">double exposure</a>.')}
  {code(ARRAY_SNIPPET)}
</section>"""

    sections: list[layout.Section] = [("base", "Base photos", 1)]
    for group, modes in groups.items():
        sections.append((f"{slugify(group)}-group", f"{group} group", 1))
        sections += [(method, method, 2) for method, _ in modes]
    sections += [("opacity", "Opacity", 1), ("colors", "Choosing a blend color", 1),
                 ("arrays", "Blending with arrays", 1)]
    return layout.page(
        filename="blend-modes.html",
        title="Blend modes",
        description="Every layeris blend mode compared on the same photos.",
        body=body,
        version=__version__,
        sections=sections,
    )


def check_api_coverage() -> None:
    """Fail the build if a public LayerImage method is missing from docs_api.py."""
    public = {
        name for name, value in vars(LayerImage).items()
        if not name.startswith("_") and isinstance(value, (staticmethod, FunctionType))
    }
    documented = {e.name for group in api.GROUPS for e in group.entries}
    missing = public - documented - set(_BLEND_METHODS)
    if missing:
        raise SystemExit(f"scripts/docs_api.py does not document: {', '.join(sorted(missing))}")


def render_api_page() -> str:
    count = str(len(BLEND_MODES))

    def entry(e: api.Entry, first: bool) -> str:
        params = ""
        if e.params:
            rows = "".join(
                f'<dt><span class="params__name">{esc(p.name)}</span>'
                f'<span class="params__type">{esc(p.type)}</span></dt>'
                f"<dd>{esc(p.description)}</dd>"
                for p in e.params
            )
            params = f'\n    <dl class="params">{rows}</dl>'
        modes = ("\n    " + layout.method_index(blend_mode_links("blend-modes.html"),
                                                  "Blend modes", "api-entry__modes")
                 if e.lists_blend_modes else "")
        example = f"\n    {code(e.code)}" if e.code else ""
        note = f" {esc(e.returns_note)}" if e.returns_note else ""
        meta = [f"<span>Returns <code>{esc(e.returns)}</code>{note}</span>"]
        meta += [f"<span>Raises <code>{esc(exc)}</code> {esc(when)}</span>" for exc, when in e.raises]
        if e.see:
            href, label = e.see
            meta.append(f'<a href="{href}">{esc(label.format(count=count))}</a>')
        return f"""
  <article class="api-entry{" api-entry--first" if first else ""}" id="{e.name}">
    <h3><a href="#{e.name}"><span class="api-entry__prefix">{esc(e.prefix)}</span><span class="api-entry__name">{e.name}</span><span class="api-entry__args">{esc(e.args)}</span></a></h3>
    <p class="api-entry__desc">{esc(e.description.format(count=count))}</p>{params}{modes}{example}
    <div class="api-entry__meta">{"".join(meta)}</div>
  </article>"""

    groups = "".join(
        f"""
<section class="section section--api" id="{g.id}">
  {section_head(g.title, esc(g.intro))}{"".join(entry(e, i == 0) for i, e in enumerate(g.entries))}
</section>"""
        for g in api.GROUPS
    )
    json_rows = "".join(
        f"<tr><td>{esc(t)}</td><td>{esc(keys)}</td><td>{esc(call)}</td></tr>"
        for t, keys, call in api.JSON_TYPES
    )
    lede = (
        "The package exports one class, <code>LayerImage</code>, and <code>__version__</code>. "
        "Operations change the image in place and return it, so calls can be chained. Call "
        "<code>clone()</code> first to keep an unchanged copy. Pixel values are floats in "
        "[0, 1]."
    )
    body = f"""{page_head("API Reference", lede)}
{layout.method_index(api_method_links(), "Methods")}
{groups}

<section class="section" id="json-types">
  {section_head("JSON Operation Types",
                'Each entry in the <code>"operations"</code> list is an object with a '
                '<code>"type"</code> and the keys below. Operations run in order. An entry '
                "with an unknown type or a missing required key is skipped without an error.")}
  <div class="table-scroll">
    <table class="json-types">
      <thead><tr><th>Type</th><th>Keys</th><th>Calls</th></tr></thead>
      <tbody>{json_rows}</tbody>
    </table>
  </div>
  <p class="section__outro">In a dict or JSON file, blend modes take a hex color only. To blend
    with a NumPy array, call the method directly.</p>
</section>"""

    sections: list[layout.Section] = []
    for g in api.GROUPS:
        sections.append((g.id, g.title[0] + g.title[1:].lower(), 1))
        sections += [(e.name, e.name, 2) for e in g.entries]
    sections.append(("json-types", "JSON operation types", 1))
    return layout.page(
        filename="api.html",
        title="API reference",
        description="Signatures, parameters and return values for every LayerImage method.",
        body=body,
        version=__version__,
        sections=sections,
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=DOCS_DIR,
        help="directory receiving the pages and images (default: docs/)",
    )
    args = parser.parse_args()
    output_dir: Path = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    check_api_coverage()
    print(f"Building docs into {output_dir}")
    written = previews.generate_previews(previews.DEFAULT_SOURCE, output_dir)
    preview_size = Image.open(written[0][1]).size

    writer = ImageWriter(output_dir)
    render_examples(writer)
    render_blend_modes(writer)

    pages = {
        "index.html": render_index(writer, preview_size),
        "examples.html": render_examples_page(writer),
        "blend-modes.html": render_blend_modes_page(writer),
        "operations.html": previews.render_operations_page(preview_size),
        "api.html": render_api_page(),
    }
    for name, content in pages.items():
        (output_dir / name).write_text(content, encoding="utf-8")
        print(f"  wrote {name}")


if __name__ == "__main__":
    main()
