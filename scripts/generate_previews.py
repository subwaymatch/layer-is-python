#!/usr/bin/env python3
"""Generate before/after preview images for every layeris operation.

This script is the single source of truth for the operation gallery. It
produces, for each operation:

  * a side-by-side before/after JPEG in ``<output-dir>/previews/``
  * a static HTML gallery at ``<output-dir>/index.html`` (GitHub Pages ready —
    enable Pages with "Deploy from a branch" and the ``/docs`` folder)

and can print the matching README markdown section with ``--markdown``.

Usage::

    python scripts/generate_previews.py                # writes into docs/
    python scripts/generate_previews.py --markdown     # also print README markdown
    python scripts/generate_previews.py --output-dir /tmp/smoke
"""

from __future__ import annotations

import argparse
import html
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from layeris import LayerImage, __version__  # noqa: E402

DEFAULT_SOURCE = REPO_ROOT / "test-images" / "piano-man-01.jpg"
PANEL_WIDTH = 480  # width of each before/after panel
GUTTER = 4  # white gap between the two panels
JPEG_QUALITY = 82

ADOBE_NOTE = (
    "Blend mode descriptions are adapted from "
    "[Adobe's blending modes documentation]"
    "(https://helpx.adobe.com/photoshop/using/blending-modes.html)."
)


@dataclass(frozen=True)
class Operation:
    slug: str  # file name and anchor
    title: str
    group: str  # gallery section
    code: str  # snippet shown in README / gallery
    apply: Callable[[LayerImage], LayerImage]
    description: str
    base: str = "color"  # "color" or "gray" — which before-image to use


OPERATIONS: list[Operation] = [
    # ------------------------------------------------------------------
    # Basic adjustments
    # ------------------------------------------------------------------
    Operation(
        slug="grayscale",
        title="Grayscale",
        group="Basic adjustments",
        code="image.grayscale()",
        apply=lambda img: img.grayscale(),
        description="Convert to grayscale using the ITU-R 601 luminance weights.",
    ),
    Operation(
        slug="brightness",
        title="Brightness",
        group="Basic adjustments",
        code="image.brightness(0.2)",
        apply=lambda img: img.brightness(0.2),
        description="Scale pixel values: a factor above 0 brightens, below 0 darkens.",
    ),
    Operation(
        slug="contrast",
        title="Contrast",
        group="Basic adjustments",
        code="image.contrast(1.5)",
        apply=lambda img: img.contrast(1.5),
        description=(
            "Expand or compress the range around mid-gray: a factor above 1 "
            "increases contrast, between 0 and 1 decreases it."
        ),
    ),
    Operation(
        slug="hue",
        title="Hue",
        group="Basic adjustments",
        code="image.hue(0.3)",
        apply=lambda img: img.hue(0.3),
        description=(
            "Set every pixel's hue to the target value in [0, 1] while keeping "
            "saturation and value — a colorize-style adjustment."
        ),
    ),
    Operation(
        slug="saturation",
        title="Saturation",
        group="Basic adjustments",
        code="image.saturation(-0.5)",
        apply=lambda img: img.saturation(-0.5),
        description=(
            "Scale color intensity: a factor above 0 boosts saturation, below 0 "
            "mutes it (-1 fully desaturates)."
        ),
    ),
    Operation(
        slug="lightness",
        title="Lightness",
        group="Basic adjustments",
        code="image.lightness(0.4)",
        apply=lambda img: img.lightness(0.4),
        description=(
            "Blend toward white (factor above 0) or black (factor below 0)."
        ),
    ),
    Operation(
        slug="curve_rgb",
        title="Curve (all channels)",
        group="Basic adjustments",
        code="image.curve('rgb', [0, 0.1, 0.4, 0.65, 0.9, 1])",
        apply=lambda img: img.curve("rgb", [0, 0.1, 0.4, 0.65, 0.9, 1]),
        description=(
            "Remap tones through control points spaced evenly across [0, 1] — "
            "here an S-curve that deepens shadows and lifts highlights."
        ),
    ),
    Operation(
        slug="curve_red",
        title="Curve (single channel)",
        group="Basic adjustments",
        code="image.curve('r', [0, 0.2, 0.8, 1])",
        apply=lambda img: img.curve("r", [0, 0.2, 0.8, 1]),
        description="The same curve machinery applied to the red channel only.",
    ),
    Operation(
        slug="resize",
        title="Resize",
        group="Basic adjustments",
        code="image.resize(width=240, height=160)",
        apply=lambda img: img.resize(240, 160),
        description="Resize with high-quality Lanczos resampling.",
    ),
    # ------------------------------------------------------------------
    # Blend modes — darken group (applied to a grayscale base, as in the
    # original demo).
    # ------------------------------------------------------------------
    Operation(
        slug="darken",
        title="Darken",
        group="Blend modes — darken",
        code="grayscale_image.darken('#3fe28f')",
        apply=lambda img: img.darken("#3fe28f"),
        base="gray",
        description=(
            "Looks at the color information in each channel and selects the base "
            "or blend color — whichever is darker — as the result color."
        ),
    ),
    Operation(
        slug="multiply",
        title="Multiply",
        group="Blend modes — darken",
        code="grayscale_image.multiply('#3fe28f')",
        apply=lambda img: img.multiply("#3fe28f"),
        base="gray",
        description=(
            "Multiplies the base color by the blend color. The result is always "
            "darker; multiplying with white leaves the color unchanged."
        ),
    ),
    Operation(
        slug="color_burn",
        title="Color Burn",
        group="Blend modes — darken",
        code="grayscale_image.color_burn('#7fe3f8')",
        apply=lambda img: img.color_burn("#7fe3f8"),
        base="gray",
        description=(
            "Darkens the base color to reflect the blend color by increasing the "
            "contrast between the two. Blending with white produces no change."
        ),
    ),
    Operation(
        slug="linear_burn",
        title="Linear Burn",
        group="Blend modes — darken",
        code="grayscale_image.linear_burn('#e1a8ff')",
        apply=lambda img: img.linear_burn("#e1a8ff"),
        base="gray",
        description=(
            "Darkens the base color to reflect the blend color by decreasing the "
            "brightness. Blending with white produces no change."
        ),
    ),
    # ------------------------------------------------------------------
    # Blend modes — lighten group
    # ------------------------------------------------------------------
    Operation(
        slug="lighten",
        title="Lighten",
        group="Blend modes — lighten",
        code="image.lighten('#ff3ce1')",
        apply=lambda img: img.lighten("#ff3ce1"),
        description=(
            "Selects the base or blend color — whichever is lighter — as the "
            "result color."
        ),
    ),
    Operation(
        slug="screen",
        title="Screen",
        group="Blend modes — lighten",
        code="image.screen('#e633ba')",
        apply=lambda img: img.screen("#e633ba"),
        description=(
            "Multiplies the inverse of the blend and base colors. The result is "
            "always lighter — like projecting multiple slides on top of each other."
        ),
    ),
    Operation(
        slug="color_dodge",
        title="Color Dodge",
        group="Blend modes — lighten",
        code="image.color_dodge('#490cc7')",
        apply=lambda img: img.color_dodge("#490cc7"),
        description=(
            "Brightens the base color to reflect the blend color by decreasing "
            "contrast between the two. Blending with black produces no change."
        ),
    ),
    Operation(
        slug="linear_dodge",
        title="Linear Dodge",
        group="Blend modes — lighten",
        code="image.linear_dodge('#490cc7')",
        apply=lambda img: img.linear_dodge("#490cc7"),
        description=(
            "Brightens the base color to reflect the blend color by increasing "
            "the brightness. Blending with black produces no change."
        ),
    ),
    # ------------------------------------------------------------------
    # Blend modes — contrast group
    # ------------------------------------------------------------------
    Operation(
        slug="overlay",
        title="Overlay",
        group="Blend modes — contrast",
        code="image.overlay('#ffb956')",
        apply=lambda img: img.overlay("#ffb956"),
        description=(
            "Multiplies or screens the colors depending on the base color, "
            "preserving its highlights and shadows."
        ),
    ),
    Operation(
        slug="soft_light",
        title="Soft Light",
        group="Blend modes — contrast",
        code="image.soft_light('#ff3cbc')",
        apply=lambda img: img.soft_light("#ff3cbc"),
        description=(
            "Darkens or lightens depending on the blend color — like shining a "
            "diffused spotlight on the image."
        ),
    ),
    Operation(
        slug="hard_light",
        title="Hard Light",
        group="Blend modes — contrast",
        code="image.hard_light('#df5dff')",
        apply=lambda img: img.hard_light("#df5dff"),
        description=(
            "Multiplies or screens depending on the blend color — like shining a "
            "harsh spotlight on the image."
        ),
    ),
    Operation(
        slug="vivid_light",
        title="Vivid Light",
        group="Blend modes — contrast",
        code="image.vivid_light('#ac5b7f')",
        apply=lambda img: img.vivid_light("#ac5b7f"),
        description=(
            "Burns or dodges by increasing or decreasing the contrast, depending "
            "on the blend color."
        ),
    ),
    Operation(
        slug="linear_light",
        title="Linear Light",
        group="Blend modes — contrast",
        code="image.linear_light('#9fa500')",
        apply=lambda img: img.linear_light("#9fa500"),
        description=(
            "Burns or dodges by decreasing or increasing the brightness, "
            "depending on the blend color."
        ),
    ),
    Operation(
        slug="pin_light",
        title="Pin Light",
        group="Blend modes — contrast",
        code="image.pin_light('#005546')",
        apply=lambda img: img.pin_light("#005546"),
        description=(
            "Replaces colors depending on the blend color — useful for adding "
            "special effects to an image."
        ),
    ),
    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------
    Operation(
        slug="chaining",
        title="Method chaining",
        group="Putting it together",
        code=(
            "(image.grayscale()\n"
            "      .brightness(0.1)\n"
            "      .multiply('#3fe28f', opacity=0.7)\n"
            "      .curve('rgb', [0, 0.1, 0.4, 0.65, 0.9, 1]))"
        ),
        apply=lambda img: (
            img.grayscale()
            .brightness(0.1)
            .multiply("#3fe28f", opacity=0.7)
            .curve("rgb", [0, 0.1, 0.4, 0.65, 0.9, 1])
        ),
        description=(
            "Every operation returns the LayerImage itself, so a whole look can "
            "be built as one chained pipeline."
        ),
    ),
]


def to_pil(image: LayerImage) -> Image.Image:
    """Convert a LayerImage to an 8-bit RGB PIL image via the public API."""
    arr = np.clip(image.get_image_as_array(), 0.0, 1.0)[:, :, :3]
    return Image.fromarray(np.round(arr * 255).astype(np.uint8), "RGB")


def side_by_side(before: Image.Image, after: Image.Image) -> Image.Image:
    """Compose the before/after panels with a thin white gutter."""
    # Smaller results (e.g. resize) sit top-left on a neutral canvas so the
    # size difference stays visible.
    if after.size != before.size:
        panel = Image.new("RGB", before.size, "#ececec")
        panel.paste(after, (0, 0))
        after = panel
    canvas = Image.new(
        "RGB",
        (before.width + GUTTER + after.width, before.height),
        "#ffffff",
    )
    canvas.paste(before, (0, 0))
    canvas.paste(after, (before.width + GUTTER, 0))
    return canvas


def generate_previews(source: Path, output_dir: Path) -> list[tuple[Operation, Path]]:
    previews_dir = output_dir / "previews"
    previews_dir.mkdir(parents=True, exist_ok=True)

    base = LayerImage.from_file(source)
    height = round(base.get_image_as_array().shape[0] * PANEL_WIDTH
                   / base.get_image_as_array().shape[1])
    base.resize(PANEL_WIDTH, height)
    bases = {"color": base, "gray": base.clone().grayscale()}
    before_panels = {kind: to_pil(img) for kind, img in bases.items()}

    written: list[tuple[Operation, Path]] = []
    for op in OPERATIONS:
        result = op.apply(bases[op.base].clone())
        composite = side_by_side(before_panels[op.base], to_pil(result))
        path = previews_dir / f"{op.slug}.jpg"
        composite.save(path, quality=JPEG_QUALITY, optimize=True)
        written.append((op, path))
        print(f"  wrote {path.relative_to(output_dir.parent) if output_dir.parent in path.parents else path}")
    return written


def render_markdown() -> str:
    """README-ready markdown for the operation gallery."""
    lines = [
        "## Operation gallery",
        "",
        "Every image below is generated by [`scripts/generate_previews.py`]"
        "(scripts/generate_previews.py) using layeris itself — the left half is "
        "the input, the right half is the result of the snippet above it. "
        "Regenerate them all with:",
        "",
        "```sh",
        "python scripts/generate_previews.py",
        "```",
        "",
        ADOBE_NOTE,
        "",
    ]
    current_group = None
    for op in OPERATIONS:
        if op.group != current_group:
            current_group = op.group
            lines += [f"### {current_group}", ""]
            if current_group == "Blend modes — darken":
                lines += [
                    "Blend modes accept a hex color string or a NumPy array, plus "
                    "an optional `opacity` (0.0–1.0). The darken-group examples "
                    "are applied to a grayscale base "
                    "(`grayscale_image = image.clone().grayscale()`), as in the "
                    "original demo.",
                    "",
                ]
        lines += [
            f"#### {op.title}",
            "",
            op.description,
            "",
            "```python",
            op.code,
            "```",
            "",
            f"![{op.slug}](docs/previews/{op.slug}.jpg)",
            "",
        ]
    return "\n".join(lines)


def render_html() -> str:
    """Static gallery page for GitHub Pages (docs/index.html)."""
    groups: dict[str, list[Operation]] = {}
    for op in OPERATIONS:
        groups.setdefault(op.group, []).append(op)

    sections = []
    for group, ops in groups.items():
        cards = []
        for op in ops:
            cards.append(f"""
      <figure class="card" id="{op.slug}">
        <figcaption>
          <h3>{html.escape(op.title)}</h3>
          <p>{html.escape(op.description)}</p>
          <pre><code>{html.escape(op.code)}</code></pre>
        </figcaption>
        <img src="previews/{op.slug}.jpg" alt="Before/after preview of {html.escape(op.title)}" loading="lazy">
      </figure>""")
        sections.append(
            f'    <section>\n      <h2>{html.escape(group)}</h2>{"".join(cards)}\n    </section>'
        )

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Layer.is — operation gallery</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0 auto; padding: 2rem 1rem 4rem; max-width: 1080px;
    font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: #1f2328; background: #ffffff;
  }}
  header p {{ color: #59636e; max-width: 60ch; }}
  h1 {{ font-size: 2rem; margin-bottom: 0.25rem; }}
  h2 {{ margin-top: 3rem; padding-bottom: 0.4rem; border-bottom: 1px solid #d1d9e0; }}
  .card {{ margin: 2rem 0; }}
  .card h3 {{ margin: 0 0 0.25rem; }}
  .card p {{ margin: 0 0 0.75rem; color: #59636e; max-width: 72ch; }}
  .card img {{ width: 100%; height: auto; border-radius: 6px; }}
  pre {{
    background: #f6f8fa; padding: 0.6rem 0.9rem; border-radius: 6px;
    overflow-x: auto; font-size: 0.875rem;
  }}
  a {{ color: #0969da; }}
  footer {{ margin-top: 4rem; font-size: 0.875rem; color: #59636e; }}
  @media (prefers-color-scheme: dark) {{
    body {{ color: #f0f6fc; background: #0d1117; }}
    header p, .card p, footer {{ color: #9198a1; }}
    h2 {{ border-color: #3d444d; }}
    pre {{ background: #151b23; }}
    a {{ color: #4493f8; }}
  }}
</style>
</head>
<body>
  <header>
    <h1>Layer.is</h1>
    <p>Photoshop-style blend modes, adjustments and curves for Python.
       Each preview shows the input on the left and the result of the snippet
       on the right — all generated with
       <a href="https://github.com/subwaymatch/layer-is-python">layeris</a> itself.</p>
  </header>
  <main>
{body}
  </main>
  <footer>Generated by <code>scripts/generate_previews.py</code> · layeris v{__version__}</footer>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=DEFAULT_SOURCE,
        help="base photo used for all previews",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=REPO_ROOT / "docs",
        help="directory receiving previews/ and index.html",
    )
    parser.add_argument(
        "--markdown", action="store_true",
        help="print the README gallery markdown to stdout",
    )
    args = parser.parse_args()

    print(f"Generating previews from {args.source} into {args.output_dir}")
    generate_previews(args.source, args.output_dir)

    index_path = args.output_dir / "index.html"
    index_path.write_text(render_html())
    print(f"  wrote {index_path}")

    if args.markdown:
        print("\n" + render_markdown())


if __name__ == "__main__":
    main()
