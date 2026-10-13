#!/usr/bin/env python3
"""Build the GitHub Pages docs site in ``docs/``.

Every result image on the site is rendered here with layeris itself, from the
sample photos in ``docs/photos/``. Recipe snippets are executed verbatim (see
``scripts/docs_examples.py``), so the code on each page is exactly the code
that produced its image. The script writes:

  * ``index.html``: landing page
  * ``examples.html``: photo recipes with before/after sliders
  * ``blend-modes.html``: every blend mode on several photos
  * ``operations.html``: every operation (via ``generate_previews.py``)

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
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from layeris import LayerImage, __version__  # noqa: E402

import docs_layout as layout  # noqa: E402  (sibling modules in scripts/)
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

# Featured on the landing page: a look switcher, then a grid of cards.
HERO_PHOTO = "vintage-car"
HERO_LOOKS = ["cross-process", "pastel-dream", "channel-swap"]
ARRAY_SNIPPET = """\
h, w, _ = image.get_image_as_array().shape
t = np.linspace(0, 1, h)[:, np.newaxis, np.newaxis]  # 0 at the top, 1 at the bottom
gradient = (1 - t) * np.array([1.0, 0.6, 0.3]) + t    # orange fading to white

image.multiply(gradient)  # white is neutral for multiply"""
FEATURED = [
    "teal-and-orange", "double-exposure", "neon-nights", "cyanotype",
    "graduated-filter", "duotone", "sepia", "lomo",
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

_BLEND_METHODS = {method for method, _, _ in BLEND_MODES}
_OPERATION_SLUGS = {op.slug for op in previews.OPERATIONS}


def operation_chips(snippet: str) -> str:
    """Chips linking each layeris method a snippet uses to its reference."""
    chips: list[str] = []
    for method in dict.fromkeys(re.findall(r"\.([a-z_]+)\(", snippet)):
        if method in _BLEND_METHODS:
            href = f"blend-modes.html#{method}"
        elif method == "curve":
            href = "operations.html#curve_rgb"
        elif method in _OPERATION_SLUGS:
            href = f"operations.html#{method}"
        else:
            continue
        chips.append(f'<a class="chip chip--code" href="{href}">{method}()</a>')
    if "np." in snippet:
        chips.append('<span class="chip">NumPy</span>')
    return f'<div class="chips">{"".join(chips)}</div>'


def recipe_compare(writer: ImageWriter, recipe: Recipe, lazy: bool = True) -> str:
    return layout.compare(
        original_path(recipe.photo),
        f"examples/{recipe.slug}.jpg",
        writer.sizes[f"examples/{recipe.slug}.jpg"],
        recipe.title,
        PHOTOS[recipe.photo].alt,
        lazy,
    )


def recipe_by_slug(slug: str) -> Recipe:
    return next(r for r in RECIPES if r.slug == slug)


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------


def render_index(writer: ImageWriter) -> str:
    looks = [("original", "Original", original_path(HERO_PHOTO),
              f'image = LayerImage.from_file("photos/{HERO_PHOTO}.jpg")')]
    looks += [
        (r.slug, r.title, f"examples/{r.slug}.jpg", r.snippet)
        for r in map(recipe_by_slug, HERO_LOOKS)
    ]
    alt = PHOTOS[HERO_PHOTO].alt
    stage = "".join(
        writer.img(src, f"{alt} ({title})", "looks__img", lazy=False).replace(
            "<img ", f'<img data-look="{key}"{" hidden" if i else ""} ', 1
        )
        for i, (key, title, src, _) in enumerate(looks)
    )
    tabs = "".join(
        f'<button type="button" class="looks__tab" data-look="{key}" '
        f'aria-pressed="{"true" if i == 0 else "false"}">{layout.esc(title)}</button>'
        for i, (key, title, _, _) in enumerate(looks)
    )
    panels = "".join(
        f'<div class="looks__panel" data-look="{key}"{" hidden" if i else ""}>'
        f"{layout.code_block(code)}</div>"
        for i, (key, _, _, code) in enumerate(looks)
    )

    cards = "".join(
        f"""
      <a class="feature" href="examples.html#{r.slug}">
        <span class="feature__media">
          {writer.img(f"examples/{r.slug}.jpg", f"{r.title} applied to the {r.photo.replace('-', ' ')} photo")}
          {writer.img(original_path(r.photo), PHOTOS[r.photo].alt, "feature__before")}
        </span>
        <span class="feature__title">{layout.esc(r.title)}</span>
        <span class="feature__meta">{layout.esc(r.category)}</span>
      </a>"""
        for r in map(recipe_by_slug, FEATURED)
    )

    quickstart = """from layeris import LayerImage

image = LayerImage.from_file("photo.jpg")
(image.grayscale()
      .brightness(0.1)
      .multiply("#3fe28f", opacity=0.7)
      .curve("rgb", [0, 0.1, 0.4, 0.65, 0.9, 1])
      .save("result.jpg"))"""

    body = f"""<div class="wrap">
  <section class="hero">
    <div class="hero__text">
      <p class="eyebrow">Image processing for Python</p>
      <h1>Photoshop-style blend modes and adjustments, in a few lines of Python.</h1>
      <p class="lede">Layer.is gives you all the common blend modes, brightness, contrast,
        hue, saturation and lightness controls, and per-channel curves, built on NumPy
        with a chainable API.</p>
      <div class="install">{layout.code_block("pip install layeris", "shell")}</div>
      <div class="cta">
        <a class="button" href="examples.html">Browse {len(RECIPES)} examples</a>
        <a class="button button--ghost" href="blend-modes.html">Explore blend modes</a>
      </div>
    </div>
    <div class="looks" data-looks>
      <div class="looks__stage">{stage}</div>
      <div class="looks__tabs" role="group" aria-label="Pick a look">{tabs}</div>
      {panels}
    </div>
  </section>

  <section class="section">
    <h2>Featured looks</h2>
    <p class="section__intro">Hover or focus a card to see the original photo. Every image is
      rendered by layeris from the snippet on the <a href="examples.html">examples page</a>.</p>
    <div class="features">{cards}
    </div>
  </section>

  <section class="section split">
    <div>
      <h2>Quick start</h2>
      <p>Load an image from a file, a URL or a NumPy array, chain operations, and save.
        Every operation mutates the image in place and returns it, so a whole look reads
        as one pipeline. Use <code>clone()</code> to branch off a copy.</p>
      <p>Requires Python 3.10+. The only dependencies are NumPy, Pillow and Requests.</p>
    </div>
    {layout.code_block(quickstart)}
  </section>

  <section class="section">
    <h2>Documentation</h2>
    <div class="cards">
      <a class="card" href="examples.html"><strong>Examples</strong>
        <span>{len(RECIPES)} complete looks (fixes, color grades, film, black &amp; white and
        creative effects), each with a before/after slider and copy-paste code.</span></a>
      <a class="card" href="blend-modes.html"><strong>Blend modes</strong>
        <span>All {len(BLEND_MODES)} blend modes side by side on three photos, plus how opacity
        and the blend color change the result.</span></a>
      <a class="card" href="operations.html"><strong>Operations</strong>
        <span>A before/after reference for every LayerImage method, from
        <code>grayscale()</code> to <code>pin_light()</code>.</span></a>
    </div>
  </section>
</div>"""
    return layout.page(
        filename="index.html",
        title="Layer.is",
        description="Photoshop-style blend modes, adjustments and curves for Python.",
        body=body,
        version=__version__,
    )


def render_examples_page(writer: ImageWriter) -> str:
    toc = "".join(
        f'<a class="chip" href="#{slugify(name)}">{layout.esc(name)} '
        f'<span class="chip__count">{sum(r.category == name for r in RECIPES)}</span></a>'
        for name, _ in CATEGORIES
    )
    sections = []
    for name, intro in CATEGORIES:
        recipes = "".join(
            f"""
    <article class="recipe" id="{r.slug}">
      <div class="recipe__media">{recipe_compare(writer, r)}</div>
      <div class="recipe__body">
        <h3><a class="anchor" href="#{r.slug}">{layout.esc(r.title)}</a></h3>
        <p>{layout.esc(r.description)}</p>
        {operation_chips(r.snippet)}
        {layout.code_block(r.snippet)}
      </div>
    </article>"""
            for r in RECIPES
            if r.category == name
        )
        sections.append(f"""  <section class="section" id="{slugify(name)}">
    <h2>{layout.esc(name)}</h2>
    <p class="section__intro">{layout.esc(intro)}</p>{recipes}
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
                        writer.sizes[f"examples/batch/{photo}.jpg"], "the warm matte preset",
                        PHOTOS[photo].alt)}
      </figure>"""
        for photo in BATCH_PHOTOS
    )
    photo_links = "".join(
        f'<a class="photo-link" href="photos/{slug}.jpg" download>'
        f'{writer.img(original_path(slug), p.alt)}<span>{slug}.jpg</span></a>'
        for slug, p in PHOTOS.items()
    )

    body = f"""<div class="wrap">
  <header class="page-head">
    <p class="eyebrow">Cookbook</p>
    <h1>Examples</h1>
    <p class="lede">{len(RECIPES)} looks built from layeris operations, each applied to a real
      photo. Drag the divider to compare. Every snippet below is the exact code that rendered
      its image, and it runs as-is: it assumes <code>from layeris import LayerImage</code>,
      <code>import numpy as np</code> and the <a href="#sample-photos">sample photos</a>
      in a <code>photos/</code> folder. Finish with <code>image.save("result.jpg")</code>.</p>
    <nav class="toc" aria-label="Categories">{toc}<a class="chip" href="#batch">Batch presets</a></nav>
  </header>
{chr(10).join(sections)}

  <section class="section" id="batch">
    <h2>One preset, many photos</h2>
    <p class="section__intro">Operations can also be described as data. Save a look as JSON and
      apply it to a whole folder with <code>apply_from_dict()</code> (or
      <code>apply_from_json()</code>). Here is a warm, matte preset on four different photos.</p>
    <div class="stack">
      {layout.code_block(preset_json, "json", "warm-matte.json")}
      {layout.code_block(batch_code, title="batch.py")}
    </div>
    <div class="batch">{batch_items}
    </div>
  </section>

  <section class="section" id="sample-photos">
    <h2>Sample photos</h2>
    <p class="section__intro">Download the originals (1536 x 1024) to run the snippets yourself.
      They were generated for these docs with OpenAI's <code>gpt-image-2.5</code> model; the
      prompts are in <code>scripts/generate_photos.py</code>.</p>
    <div class="photos">{photo_links}</div>
  </section>
</div>"""
    return layout.page(
        filename="examples.html",
        title="Examples",
        description=f"{len(RECIPES)} photo recipes built with layeris, with before/after sliders.",
        body=body,
        version=__version__,
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

    swatch = (f'<span class="swatch" style="background:{BLEND_COLOR}"></span>'
              f"<code>{BLEND_COLOR}</code>")
    base_row = "".join(
        f"<figure>{writer.img(f'blend-modes/{photo}.jpg', PHOTOS[photo].alt)}"
        f"<figcaption>{photo}</figcaption></figure>"
        for photo in BLEND_PHOTOS
    )
    toc = "".join(
        f'<a class="chip chip--code" href="#{method}">{method}</a>'
        for method, _, _ in BLEND_MODES
    )

    def mode_card(method: str, formula: str) -> str:
        thumbs = "".join(
            writer.img(mode_path(photo, method),
                       f"{method_title(method)} with {BLEND_COLOR} on the {photo} photo")
            for photo in BLEND_PHOTOS
        )
        code = layout.code_block(f'image.{method}("{BLEND_COLOR}")')
        return f"""
      <article class="mode" id="{method}">
        <header class="mode__head">
          <h3><a class="anchor" href="#{method}">{method_title(method)}</a></h3>
          <code class="formula">{layout.esc(formula)}</code>
        </header>
        <div class="mode__thumbs">{thumbs}</div>
        {code}
      </article>"""

    sections = []
    for group, modes in groups.items():
        cards = "".join(mode_card(method, formula) for method, formula in modes)
        sections.append(f"""  <section class="section" id="{slugify(group)}">
    <h2>{group} group</h2>
    <p class="section__intro">{group_intros[group]}</p>
    <div class="modes">{cards}
    </div>
  </section>""")

    opacity_strip = "".join(
        f"<figure>{writer.img(opacity_path(o), f'{method_title(OPACITY_MODE)} at opacity {o:g}')}"
        f"<figcaption><code>opacity={o:g}</code></figcaption></figure>"
        for o in OPACITY_STEPS
    )
    color_strip = "".join(
        f"<figure>{writer.img(color_path(c), f'{method_title(COLOR_MODE)} with {c}')}"
        f'<figcaption><span class="swatch" style="background:{c}"></span>'
        f"<code>{c}</code></figcaption></figure>"
        for c in COLOR_SWATCHES
    )
    array_code = layout.code_block(ARRAY_SNIPPET)

    body = f"""<div class="wrap">
  <header class="page-head">
    <p class="eyebrow">Reference</p>
    <h1>Blend modes</h1>
    <p class="lede">A blend mode combines the image (the base, <em>A</em>) with a blend layer
      (<em>B</em>). The layer can be a hex color, a NumPy array the same size as the image
      (a gradient, a texture, another photo) or anything that broadcasts to it. Every mode
      takes an optional <code>opacity</code> from 0 to 1. Below, all {len(BLEND_MODES)} modes
      blend {swatch} into the same three photos.</p>
    <nav class="toc" aria-label="Blend modes">{toc}</nav>
  </header>

  <section class="section">
    <h2>Base photos</h2>
    <p class="section__intro">The unedited photos that every blend mode below is applied to.</p>
    <div class="strip strip--3">{base_row}</div>
  </section>

{chr(10).join(sections)}

  <section class="section" id="opacity">
    <h2>Opacity</h2>
    <p class="section__intro">Opacity mixes the blended result back with the original:
      <code>{OPACITY_MODE}("{OPACITY_COLOR}", opacity=...)</code> on the {OPACITY_PHOTO} photo.</p>
    <div class="strip strip--5">{opacity_strip}</div>
  </section>

  <section class="section" id="colors">
    <h2>Choosing a blend color</h2>
    <p class="section__intro">The same mode gives very different moods depending on the color:
      <code>{COLOR_MODE}(color)</code> on the {COLOR_PHOTO} photo.</p>
    <div class="strip strip--6">{color_strip}</div>
  </section>

  <section class="section" id="arrays">
    <h2>Blending with arrays</h2>
    <p class="section__intro">Pass a NumPy array instead of a hex string to blend per pixel.
      The <a href="examples.html#creative-effects">creative effects</a> examples use this for
      a <a href="examples.html#lomo">vignette</a>, a
      <a href="examples.html#graduated-filter">graduated filter</a> and a
      <a href="examples.html#double-exposure">double exposure</a>.</p>
    {array_code}
  </section>
</div>"""
    return layout.page(
        filename="blend-modes.html",
        title="Blend modes",
        description="Every layeris blend mode compared on the same photos.",
        body=body,
        version=__version__,
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

    print(f"Building docs into {output_dir}")
    written = previews.generate_previews(previews.DEFAULT_SOURCE, output_dir)
    preview_size = Image.open(written[0][1]).size

    writer = ImageWriter(output_dir)
    render_examples(writer)
    render_blend_modes(writer)

    pages = {
        "index.html": render_index(writer),
        "examples.html": render_examples_page(writer),
        "blend-modes.html": render_blend_modes_page(writer),
        "operations.html": previews.render_operations_page(preview_size),
    }
    for name, content in pages.items():
        (output_dir / name).write_text(content, encoding="utf-8")
        print(f"  wrote {name}")


if __name__ == "__main__":
    main()
