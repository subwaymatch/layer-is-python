#!/usr/bin/env python3
"""Generate the video's background music with the ElevenLabs Music API.

Each style below is an instrumental prompt sized to the video's exact length.
The render only *reads* ``video/public/music.mp3``, so this script is needed
only to replace the track. Every run gives a different take, even for the
same style.

Usage::

    export ELEVENLABS_API_KEY=...
    python video/scripts/generate_music.py                     # default style
    python video/scripts/generate_music.py --style lofi --out /tmp/lofi.mp3
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

# Shared by every style: what the track is for, and what to avoid.
BRIEF = (
    "Background music for a calm, minimal walkthrough video of a software "
    "library. Clean, polished production with a spacious, airy mix. "
    "Instrumental only: no vocals, no drops, no cinematic swells, nothing "
    "corporate or cheesy."
)

STYLES: dict[str, str] = {
    "piano": (
        "Warm, minimal modern instrumental. Soft felt piano plays a simple, "
        "hopeful chord progression, joined by gentle plucked synth arpeggios, "
        "a light crisp beat with a soft kick, brushed snare and shaker, and a "
        "round, warm bass. Around 100 BPM, optimistic but understated. It "
        "starts with solo piano, the beat comes in after a few seconds, it "
        "grows slightly fuller in the middle, and it ends on a soft final "
        "piano chord that rings out."
    ),
    "marimba": (
        "Light, playful minimal electronic instrumental. Marimba and kalimba "
        "plucks trade a bright, curious motif over soft synth pads, finger "
        "snaps, a gentle bouncy beat and a warm bass. Around 110 BPM, "
        "friendly and focused. It opens with a solo marimba, builds lightly, "
        "and ends on a clean final note that rings out."
    ),
    "lofi": (
        "Mellow lo-fi chillhop instrumental. Jazzy Rhodes electric piano "
        "chords over a soft, laid-back boom-bap beat with a slight swing, a "
        "warm upright bass and subtle vinyl texture. Around 85 BPM, relaxed, "
        "cozy and focused. It opens with the Rhodes alone, the beat drops in "
        "after a few seconds, and it ends with the last chord ringing out."
    ),
}
DEFAULT_STYLE = "piano"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--style", choices=sorted(STYLES), default=DEFAULT_STYLE,
                        help=f"prompt to use (default: {DEFAULT_STYLE})")
    parser.add_argument("--model", default=MODEL, help=f"model id (default: {MODEL})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output MP3 path")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY is not set")

    print(f"Generating {LENGTH_MS / 1000:.1f} s of '{args.style}' music with {args.model}")
    response = requests.post(
        "https://api.elevenlabs.io/v1/music",
        headers={"xi-api-key": api_key},
        json={
            "prompt": f"{STYLES[args.style]} {BRIEF}",
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
