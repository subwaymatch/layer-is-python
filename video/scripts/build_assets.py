#!/usr/bin/env python3
"""Render every edited image shown in the layeris video, using layeris itself.

The video never fakes an edit: each image on screen is produced here from the
photos in ``video/public/photos/``, and the code shown next to it is the code
that ran. Results go to ``video/public/renders/`` and a manifest the video
imports goes to ``video/src/data/assets.json``.

Usage (from the repository root, with layeris installed)::

    pip install -e .
    python video/scripts/build_assets.py
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from layeris import LayerImage

VIDEO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = VIDEO_ROOT / "public"
PHOTOS_DIR = PUBLIC_DIR / "photos"
RENDERS_DIR = PUBLIC_DIR / "renders"
MANIFEST = VIDEO_ROOT / "src" / "data" / "assets.json"

JPEG_QUALITY = 88

# ----------------------------------------------------------------------
# Scene: chained operations
# ----------------------------------------------------------------------

CHAIN_PHOTO = "vase"
CHAIN_SIZE = (1152, 768)
CHAIN_STEPS: list[str] = [
    "grayscale()",
    "contrast(1.2)",
    'multiply("#f2c49b", opacity=0.8)',
    'curve("b", [0.12, 0.4, 0.7, 0.92])',
]
CHAIN_SAVE_AS = "vase-toned.jpg"

# ----------------------------------------------------------------------
# Scene: blend modes
# ----------------------------------------------------------------------

BLEND_PHOTO = "dunes"
BLEND_SIZE = (480, 320)
BLEND_COLOR = "#e8743b"
BLEND_MODES: list[str] = [
    "darken", "multiply", "color_burn", "linear_burn",
    "lighten", "screen", "color_dodge", "linear_dodge",
    "overlay", "soft_light", "hard_light", "vivid_light", "linear_light", "pin_light",
]

# ----------------------------------------------------------------------
# Scene: per-channel curves
# ----------------------------------------------------------------------

CURVES_PHOTO = "tree"
CURVES_SIZE = (1008, 672)
# Each phase eases one channel's control points from a straight line to the
# target. Phases apply on top of each other, in order.
CURVE_PHASES: list[tuple[str, list[float]]] = [
    ("r", [0, 0.1, 0.5, 0.9, 1]),
    ("b", [0.2, 0.36, 0.5, 0.62, 0.78]),
]
# Images rendered per phase; the video crossfades between neighbours.
CURVE_STEPS = 21

# ----------------------------------------------------------------------
# Scene: looks (recipes adapted from the docs' examples page)
# ----------------------------------------------------------------------

LOOKS_SIZE = (1152, 768)
LOOKS: list[dict[str, Any]] = [
    {
        "slug": "cross-process",
        "title": "Cross-processed",
        "photo": "lemons",
        "code": """
(image.curve("r", [0, 0.15, 0.55, 0.9, 1])
      .curve("g", [0, 0.2, 0.55, 0.85, 1])
      .curve("b", [0.22, 0.35, 0.48, 0.6, 0.72]))
""",
    },
    {
        "slug": "cyanotype",
        "title": "Cyanotype",
        "photo": "lighthouse",
        "code": """
(image.grayscale()
      .curve("rgb", [0, 0.1, 0.55, 0.9, 1])
      .curve("r", [0.02, 0.85])
      .curve("g", [0.15, 0.95])
      .curve("b", [0.35, 1.0]))
""",
    },
    {
        "slug": "duotone",
        "title": "Duotone, from a JSON preset",
        "photo": "stairs",
        "preset": {
            "operations": [
                {"type": "grayscale"},
                {"type": "contrast", "factor": 1.2},
                {"type": "curve", "channels": "r", "curve_points": [0.12, 1.0]},
                {"type": "curve", "channels": "g", "curve_points": [0.08, 0.45]},
                {"type": "curve", "channels": "b", "curve_points": [0.4, 0.42]},
            ]
        },
        "code": 'image.apply_from_json("duotone.json")',
    },
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def load(photo: str, size: tuple[int, int]) -> LayerImage:
    return LayerImage.from_file(PHOTOS_DIR / f"{photo}.jpg").resize(*size)


def save(image: LayerImage, rel: str) -> str:
    path = RENDERS_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=JPEG_QUALITY)
    return f"renders/{rel}"


def run(snippet: str, image: LayerImage) -> LayerImage:
    """Execute *snippet* exactly as shown on screen, with ``image`` in scope."""
    scope: dict[str, Any] = {"LayerImage": LayerImage, "image": image}
    exec(snippet, scope)  # noqa: S102 - trusted, hard-coded snippets
    return scope["image"]


def format_preset(preset: dict[str, Any]) -> str:
    """JSON with one operation per line, so the preset fits on screen."""
    ops = ",\n".join(f"    {json.dumps(op)}" for op in preset["operations"])
    return '{\n  "operations": [\n' + ops + "\n  ]\n}"


def lerp(a: list[float], b: list[float], t: float) -> list[float]:
    return [x + (y - x) * t for x, y in zip(a, b)]


def straight(n: int) -> list[float]:
    return [i / (n - 1) for i in range(n)]


# ----------------------------------------------------------------------
# Builders
# ----------------------------------------------------------------------


def build_chain() -> dict[str, Any]:
    image = load(CHAIN_PHOTO, CHAIN_SIZE)
    frames = [save(image, "chain/0-original.jpg")]
    for i, step in enumerate(CHAIN_STEPS, start=1):
        image = run(f"image.{step}", image)
        frames.append(save(image, f"chain/{i}-{step.split('(')[0]}.jpg"))
    return {
        "photo": f"{CHAIN_PHOTO}.jpg",
        "steps": CHAIN_STEPS,
        "saveAs": CHAIN_SAVE_AS,
        "images": frames,
    }


def build_blend() -> dict[str, Any]:
    base = load(BLEND_PHOTO, BLEND_SIZE)
    tiles = [{"mode": "original", "image": save(base, "blend/original.jpg")}]
    for mode in BLEND_MODES:
        result = getattr(base.clone(), mode)(BLEND_COLOR)
        tiles.append({"mode": mode, "image": save(result, f"blend/{mode}.jpg")})
    return {"photo": f"{BLEND_PHOTO}.jpg", "color": BLEND_COLOR, "tiles": tiles}


def build_curves() -> dict[str, Any]:
    base = load(CURVES_PHOTO, CURVES_SIZE)
    phases = []
    for p, (channels, target) in enumerate(CURVE_PHASES):
        start = straight(len(target))
        images = []
        for step in range(CURVE_STEPS):
            t = step / (CURVE_STEPS - 1)
            image = base.clone().curve(channels, lerp(start, target, t))
            images.append(save(image, f"curves/{p}-{channels}-{step:02d}.jpg"))
        phases.append(
            {"channels": channels, "start": start, "target": target, "images": images}
        )
        # The next phase builds on top of this one, as chained calls would.
        base.curve(channels, target)
    return {"photo": f"{CURVES_PHOTO}.jpg", "phases": phases}


def build_looks() -> list[dict[str, Any]]:
    presets_dir = RENDERS_DIR / "presets"
    presets_dir.mkdir(parents=True, exist_ok=True)
    looks = []
    for look in LOOKS:
        image = load(look["photo"], LOOKS_SIZE)
        before = save(image, f"looks/{look['slug']}-before.jpg")
        preset_text = None
        cwd = os.getcwd()
        try:
            if "preset" in look:
                preset_text = format_preset(look["preset"])
                assert json.loads(preset_text) == look["preset"]
                (presets_dir / f"{look['slug']}.json").write_text(preset_text + "\n")
                os.chdir(presets_dir)  # so the snippet's relative path resolves
            image = run(look["code"].strip(), image)
        finally:
            os.chdir(cwd)
        after = save(image, f"looks/{look['slug']}-after.jpg")
        looks.append(
            {
                "slug": look["slug"],
                "title": look["title"],
                "photo": f"{look['photo']}.jpg",
                "code": look["code"].strip(),
                "preset": preset_text,
                "before": before,
                "after": after,
            }
        )
    return looks


def main() -> None:
    if RENDERS_DIR.exists():
        shutil.rmtree(RENDERS_DIR)
    manifest = {
        "chain": build_chain(),
        "blend": build_blend(),
        "curves": build_curves(),
        "looks": build_looks(),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    count = sum(1 for _ in RENDERS_DIR.rglob("*.jpg"))
    print(f"Wrote {count} images to {RENDERS_DIR.relative_to(VIDEO_ROOT)}/")
    print(f"Wrote {MANIFEST.relative_to(VIDEO_ROOT)}")


if __name__ == "__main__":
    main()
