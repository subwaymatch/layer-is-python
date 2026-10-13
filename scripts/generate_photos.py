#!/usr/bin/env python3
"""Generate the sample photos used by the docs site's examples.

Every photo in ``docs/photos/`` was created with OpenAI's Images API from the
prompt listed in ``PHOTOS`` below, so the set can be reproduced or extended.
The docs build (``scripts/build_docs.py``) only *reads* these files — it never
calls the API — so this script is needed only when adding or replacing photos.

Usage::

    export OPENAI_API_KEY=...
    python scripts/generate_photos.py                  # generate missing photos
    python scripts/generate_photos.py --force          # regenerate all of them
    python scripts/generate_photos.py --only forest    # regenerate one photo
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

REPO_ROOT = Path(__file__).resolve().parent.parent
PHOTOS_DIR = REPO_ROOT / "docs" / "photos"

MODEL = "gpt-image-2.5-flare"
QUALITY = "low"
SIZE = "1536x1024"
JPEG_QUALITY = 85

# Shared suffix that keeps the photos natural-looking: heavily stylised
# source images would leave little room to show what each edit does.
STYLE = (
    "Realistic documentary photograph, natural unedited colors, neutral color "
    "grading, no text, no watermark."
)

PHOTOS: dict[str, str] = {
    "mountain-lake": (
        "An alpine lake at sunrise, pine trees on the rocky shore, snow-capped "
        "mountains reflected in calm water, soft morning light."
    ),
    "portrait": (
        "Environmental portrait of a smiling older man with a grey beard and a "
        "knitted wool cap, sitting by a window in a workshop, soft natural "
        "window light from the side, shallow depth of field."
    ),
    "city-night": (
        "A rainy city street at night, wet asphalt reflecting neon shop signs "
        "and street lights, a few pedestrians with umbrellas, taxis passing."
    ),
    "breakfast": (
        "Overhead flat-lay of a breakfast table: avocado toast, a bowl of "
        "berries and yogurt, a cup of coffee, orange juice, on a light wooden "
        "table, daylight."
    ),
    "flower-market": (
        "A colorful flower stall at an outdoor market with buckets of tulips, "
        "roses, sunflowers and peonies, a vendor arranging bouquets in the "
        "background, daylight."
    ),
    "architecture": (
        "Modern white concrete building with repeating curved balconies, shot "
        "from below against a clear blue sky, strong geometric shapes and "
        "shadows, midday sun."
    ),
    "beach": (
        "A wide sandy beach in the late afternoon, gentle waves, a lifeguard "
        "tower, two people walking along the waterline, a few clouds."
    ),
    "forest": (
        "A misty pine forest in the early morning, tall straight trunks, light "
        "fog between the trees, ferns and moss on the ground, sun rays."
    ),
    "cafe": (
        "Interior of a cozy neighborhood cafe, a barista behind the counter "
        "preparing coffee, wooden furniture, plants, warm pendant lights and "
        "daylight from large windows."
    ),
    "vintage-car": (
        "A classic 1960s turquoise car parked on a colorful old-town street "
        "with pastel painted houses, cobblestones, sunny afternoon."
    ),
    "harbor": (
        "A small fishing harbor on a hazy overcast day, wooden boats moored at "
        "a pier, flat soft light, low contrast, muted colors, slightly washed "
        "out."
    ),
    "silhouette": (
        "Side profile of a young woman's head and shoulders, centered, a dark "
        "silhouette against a plain bright white overcast sky, minimal, high "
        "key background."
    ),
    "snowy-cabin": (
        "A small wooden cabin in a snowy landscape on a winter morning, snow on "
        "the roof and spruce trees, smoke rising from the chimney, footprints "
        "in the snow."
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
            print(f"  wrote {future.result().relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
