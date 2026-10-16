#!/usr/bin/env python3
"""Generate the source photos used by the layeris video.

Every photo in ``video/public/photos/`` was created with OpenAI's Images API
from the prompt listed in ``PHOTOS`` below. The render only *reads* these
files, so this script is needed only when adding or replacing photos.

Usage::

    export OPENAI_API_KEY=...
    python video/scripts/generate_photos.py               # generate missing photos
    python video/scripts/generate_photos.py --force       # regenerate all of them
    python video/scripts/generate_photos.py --only vase   # regenerate one photo
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

VIDEO_ROOT = Path(__file__).resolve().parent.parent
PHOTOS_DIR = VIDEO_ROOT / "public" / "photos"

MODEL = "gpt-image-2.5-flare"
QUALITY = "low"
SIZE = "1536x1024"
JPEG_QUALITY = 90

# Minimal, clean compositions with a full tonal range, so every edit in the
# video has room to show what it does.
STYLE = (
    "Minimal, clean composition with generous negative space, realistic "
    "photograph, natural unedited colors, neutral color grading, no text, no "
    "watermark."
)

PHOTOS: dict[str, str] = {
    "vase": (
        "A single white ceramic vase holding one dried branch on a pale oak "
        "table against a plain warm grey plaster wall, soft window light from "
        "the left casting a long gentle shadow."
    ),
    "dunes": (
        "Smooth sand dunes with one clean curved ridgeline under a clear pale "
        "blue sky, late afternoon side light, crisp shadow on one side."
    ),
    "stairs": (
        "A white curved concrete staircase on the side of a modern building "
        "against a clear deep blue sky, strong geometric shadows, midday sun."
    ),
    "lemons": (
        "Three lemons with a few green leaves on a pale blue tabletop, shot "
        "from directly above, hard sunlight with crisp shadows."
    ),
    "lighthouse": (
        "A lone white lighthouse on a grassy headland above a calm sea, pale "
        "overcast sky, small in the frame."
    ),
    "chair": (
        "A single mid-century wooden chair in an empty room with white walls "
        "and a light wooden floor, sunlight through a window casting a soft "
        "shadow pattern on the wall."
    ),
    "tree": (
        "A lone tree on a gently rolling green hill under a soft pale sky, "
        "early morning light, wide shot."
    ),
}


def generate(slug: str, prompt: str, api_key: str) -> Path:
    response = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "prompt": f"{prompt} {STYLE}",
            "size": SIZE,
            "quality": QUALITY,
            "n": 1,
        },
        timeout=300,
    )
    response.raise_for_status()
    png = base64.b64decode(response.json()["data"][0]["b64_json"])
    path = PHOTOS_DIR / f"{slug}.jpg"
    Image.open(BytesIO(png)).convert("RGB").save(
        path, quality=JPEG_QUALITY, optimize=True, progressive=True
    )
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="regenerate photos that already exist"
    )
    parser.add_argument(
        "--only", nargs="+", choices=sorted(PHOTOS), metavar="SLUG",
        help="generate only these photos (implies --force for them)",
    )
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY is not set")

    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    if args.only:
        todo = {slug: PHOTOS[slug] for slug in args.only}
    else:
        todo = {
            slug: prompt for slug, prompt in PHOTOS.items()
            if args.force or not (PHOTOS_DIR / f"{slug}.jpg").exists()
        }
    if not todo:
        print("All photos already exist; pass --force to regenerate.")
        return

    print(f"Generating {len(todo)} photo(s) with {MODEL} (quality={QUALITY})")
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            slug: pool.submit(generate, slug, prompt, api_key)
            for slug, prompt in todo.items()
        }
        for slug, future in futures.items():
            print(f"  wrote {future.result().relative_to(VIDEO_ROOT)}")


if __name__ == "__main__":
    main()
