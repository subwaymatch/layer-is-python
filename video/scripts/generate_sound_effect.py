#!/usr/bin/env python3
"""Generate the sound effect that plays as the logo appears.

Uses the ElevenLabs Sound Effects API. The render only *reads*
``video/public/logo.mp3``, so this script is needed only to replace it.

Usage::

    export ELEVENLABS_API_KEY=...
    python video/scripts/generate_sound_effect.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

VIDEO_ROOT = Path(__file__).resolve().parent.parent
OUT = VIDEO_ROOT / "public" / "logo.mp3"

# The logo's outlines draw in over the first ~0.7 s and its layers settle by
# ~1.2 s (see src/components/logoMotion.ts, played at 2x in the intro).
DURATION_SECONDS = 2.0
PROMPT = (
    "A soft, airy shimmer that rises gently and settles into a single warm, "
    "glassy chime, like translucent layers sliding together. Clean, minimal, "
    "modern interface sound, subtle and elegant, with a short natural tail."
)


def main() -> None:
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY is not set")

    print(f"Generating a {DURATION_SECONDS:.1f} s sound effect")
    response = requests.post(
        "https://api.elevenlabs.io/v1/sound-generation",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": api_key},
        json={
            "text": PROMPT,
            "duration_seconds": DURATION_SECONDS,
            "prompt_influence": 0.6,
        },
        timeout=300,
    )
    if not response.ok:
        sys.exit(f"ElevenLabs returned {response.status_code}: {response.text[:500]}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(response.content)
    print(f"  wrote {OUT} ({len(response.content) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
