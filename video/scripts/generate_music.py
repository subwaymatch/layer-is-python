#!/usr/bin/env python3
"""Generate the video's background music with the ElevenLabs Music API.

The track is instrumental gugak (Korean traditional music) in the manner of
gayageum ensemble arrangements of Pachelbel's Canon, generated at the video's
exact length. The render only *reads* ``video/public/music.mp3``, so this
script is needed only to replace the track.

Usage::

    export ELEVENLABS_API_KEY=...
    python video/scripts/generate_music.py
    python video/scripts/generate_music.py --model music_v1 --out /tmp/try.mp3
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

VIDEO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = VIDEO_ROOT / "public" / "music.mp3"

MODEL = "music_v2_5"
# The composition's length: 1,563 frames at 30 fps (see src/Video.tsx).
LENGTH_MS = 52_100

# In the manner of Korean gayageum ensemble arrangements of Pachelbel's
# Canon. The API rejects prompts that name a piece, so this one describes the
# music instead: the Canon's ground bass (public domain) and the canon texture.
PROMPT = (
    "An instrumental piece of Korean traditional music (gugak) played by a "
    "gayageum ensemble, built on a baroque-style repeating eight-chord "
    "ground bass in D major (D, A, B minor, F-sharp minor, G, D, G, A). "
    "Several gayageums (12-string Korean zithers) enter one after another "
    "in canon over the progression, each variation livelier than the last, "
    "with bright plucked arpeggios, cascading runs, gentle vibrato and "
    "expressive pitch bends. The janggu (hourglass drum) keeps a light, "
    "steady beat, low geomungo plucks double the bass line, and the daegeum "
    "(bamboo flute) and haegeum (two-string fiddle) join with soaring "
    "melodic lines in the later variations. Bright, graceful and uplifting, "
    "with clean modern production and a moderate tempo around 90 BPM. It "
    "opens with a solo gayageum playing the progression, builds gradually "
    "through the variations, and ends on a full, resolved final chord that "
    "rings out. No vocals."
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=MODEL, help=f"model id (default: {MODEL})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output MP3 path")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY is not set")

    print(f"Generating {LENGTH_MS / 1000:.1f} s of music with {args.model}")
    response = requests.post(
        "https://api.elevenlabs.io/v1/music",
        headers={"xi-api-key": api_key},
        json={
            "prompt": PROMPT,
            "music_length_ms": LENGTH_MS,
            "model_id": args.model,
            "force_instrumental": True,
        },
        timeout=600,
    )
    if not response.ok:
        sys.exit(f"ElevenLabs returned {response.status_code}: {response.text[:500]}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(response.content)
    song_id = response.headers.get("song-id") or response.headers.get("x-song-id")
    print(f"  wrote {args.out} ({len(response.content) / 1024:.0f} KB)"
          + (f", song id {song_id}" if song_id else ""))


if __name__ == "__main__":
    main()
