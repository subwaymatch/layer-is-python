#!/usr/bin/env python3
"""Generate the sample photos used by the docs site's examples.

Every photo in ``docs/photos/`` was created with OpenAI's Images API from the
prompt listed in ``PHOTOS`` below, so the set can be reproduced or extended.
The docs build (``scripts/build_docs.py``) only *reads* these files and never
calls the API, so this script is needed only when adding or replacing photos.

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

# Shared suffix: minimal, clean compositions that still look natural, since
# heavily stylised source images would leave little room to show what each
# edit does. Every photo shows something from Korea.
STYLE = (
    "Minimal, clean composition with generous negative space. Realistic "
    "documentary photograph, natural unedited colors, neutral color grading, "
    "no text, no watermark."
)

PHOTOS: dict[str, str] = {
    "palace-pond": (
        "Gyeonghoeru, the pavilion of Gyeongbokgung Palace in Seoul, reflected "
        "in its calm pond at sunrise, soft pink and orange sky, mountains in "
        "the distance."
    ),
    "hanbok-portrait": (
        "Environmental portrait of a smiling older Korean man with a grey "
        "beard, wearing a white hanbok and a traditional black horsehair gat "
        "hat, sitting by a hanji paper window, soft cool daylight from the "
        "side, shallow depth of field."
    ),
    "seoul-night": (
        "A narrow alley in Seoul at night after rain, glowing neon shop signs "
        "and red paper lanterns reflected on the wet pavement, a few "
        "pedestrians with umbrellas. The signs are blurred, with no legible "
        "lettering."
    ),
    "bibimbap": (
        "Overhead flat-lay of a Korean meal on a light wooden table: bibimbap "
        "in a hot stone bowl topped with a fried egg, small dishes of banchan "
        "and kimchi, a bowl of rice, metal chopsticks and a spoon, daylight."
    ),
    "lotus-lanterns": (
        "Rows of colorful lotus lanterns in pink, red, yellow, green and blue "
        "hanging over a Korean temple courtyard for Buddha's Birthday, "
        "daylight."
    ),
    "palace-eaves": (
        "The upturned eaves of a Korean palace roof painted with colorful "
        "dancheong patterns, shot from below against a clear deep blue sky, "
        "strong geometric shapes and shadows, midday sun."
    ),
    "jeju-coast": (
        "A beach on Jeju Island in the late afternoon, black volcanic rocks in "
        "the foreground, turquoise water and gentle waves, two people walking "
        "along the waterline, a few clouds."
    ),
    "bamboo-forest": (
        "A misty bamboo forest in the early morning, tall straight green "
        "stalks, light fog between them, sun rays."
    ),
    "hanok-tea": (
        "A pale green celadon tea set on a low wooden table inside a hanok "
        "room, hanji paper sliding doors, warm wooden floor, soft daylight."
    ),
    "gamcheon-village": (
        "Brightly painted pastel houses in pink, turquoise, yellow and blue "
        "stacked on a hillside in Gamcheon Culture Village, Busan, sunny "
        "afternoon, clear sky."
    ),
    "fishing-harbor": (
        "A small fishing harbor on Korea's east coast on a hazy overcast day, "
        "wooden fishing boats moored at a pier, flat soft light, low contrast, "
        "muted colors, slightly washed out."
    ),
    "hanbok-silhouette": (
        "Side profile of a young woman's head and shoulders, wearing a hanbok, "
        "her hair in a traditional low bun with a binyeo hairpin, centered, a "
        "dark silhouette against a plain bright white overcast sky, minimal, "
        "high key background."
    ),
    "snowy-hanok": (
        "A traditional hanok house with a curved tiled roof covered in snow on "
        "a winter morning, a stone wall and pine trees, smoke rising from the "
        "chimney, footprints in the snow."
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
