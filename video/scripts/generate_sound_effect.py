#!/usr/bin/env python3
"""Generate the video's sound effects with the ElevenLabs Sound Effects API.

* ``logo``: plays as the logo appears (``video/public/logo.mp3``).
* ``key``: one keystroke, played for each letter as the wordmark is typed
  (``video/public/key.mp3``). It is trimmed to start right at the click and
  normalized to a -6 dBFS peak.

The render only *reads* these files, so this script is needed only to replace
one. Name the effects to generate; each run gives a different take.

Usage::

    export ELEVENLABS_API_KEY=...
    python video/scripts/generate_sound_effect.py key
    python video/scripts/generate_sound_effect.py logo key
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import requests

VIDEO_ROOT = Path(__file__).resolve().parent.parent
PUBLIC_DIR = VIDEO_ROOT / "public"
# Trimmed effects are normalized to this peak; the mix sets their level.
TRIMMED_PEAK_DB = -6.0


@dataclass(frozen=True)
class Effect:
    prompt: str
    duration_seconds: float
    # Seconds to keep after the first sound, or None to keep the whole clip.
    trim_to: float | None = None


EFFECTS: dict[str, Effect] = {
    # The logo's outlines draw in over the first ~0.7 s and its layers settle
    # by ~1.2 s (see src/components/logoMotion.ts, played at 2x in the intro).
    "logo": Effect(
        prompt=(
            "A soft, airy shimmer that rises gently and settles into a single "
            "warm, glassy chime, like translucent layers sliding together. "
            "Clean, minimal, modern interface sound, subtle and elegant, with "
            "a short natural tail."
        ),
        duration_seconds=2.0,
    ),
    # Letters are typed 2 frames (67 ms) apart, so each click must be short.
    "key": Effect(
        prompt=(
            "A single soft keystroke on a quiet, premium laptop keyboard: one "
            "short, crisp, muted click, close up, in a silent room. Nothing "
            "else."
        ),
        duration_seconds=0.5,
        trim_to=0.12,
    ),
}


def generate(name: str, effect: Effect, api_key: str) -> Path:
    response = requests.post(
        "https://api.elevenlabs.io/v1/sound-generation",
        params={"output_format": "mp3_44100_128"},
        headers={"xi-api-key": api_key},
        json={
            "text": effect.prompt,
            "duration_seconds": effect.duration_seconds,
            "prompt_influence": 0.6,
        },
        timeout=300,
    )
    if not response.ok:
        sys.exit(f"ElevenLabs returned {response.status_code}: {response.text[:500]}")
    out = PUBLIC_DIR / f"{name}.mp3"
    out.parent.mkdir(parents=True, exist_ok=True)
    if effect.trim_to is None:
        out.write_bytes(response.content)
        return out
    # Drop the silence before the sound, keep `trim_to` seconds of it, fade
    # the end so the clip doesn't click when it stops, then normalize the peak.
    with tempfile.NamedTemporaryFile(suffix=".mp3") as raw:
        raw.write(response.content)
        raw.flush()
        fade = min(0.04, effect.trim_to / 3)
        trim = (
            "silenceremove=start_periods=1:start_threshold=-45dB,"
            f"atrim=0:{effect.trim_to},"
            f"afade=t=out:st={effect.trim_to - fade}:d={fade}"
        )
        gain = TRIMMED_PEAK_DB - peak_db(raw.name, trim)
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", raw.name,
             "-af", f"{trim},volume={gain:.1f}dB", "-b:a", "128k", str(out)],
            check=True,
        )
    return out


def peak_db(path: str, filters: str) -> float:
    """Peak level in dBFS of `path` after `filters`, measured by ffmpeg."""
    result = subprocess.run(
        ["ffmpeg", "-nostats", "-i", path, "-af", f"{filters},volumedetect",
         "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    )
    return float(re.search(r"max_volume: (-?[\d.]+) dB", result.stderr).group(1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("names", nargs="+", choices=sorted(EFFECTS), metavar="EFFECT",
                        help=f"effects to generate: {', '.join(EFFECTS)}")
    args = parser.parse_args()

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        sys.exit("ELEVENLABS_API_KEY is not set")

    for name in args.names:
        path = generate(name, EFFECTS[name], api_key)
        print(f"  wrote {path.relative_to(VIDEO_ROOT)} ({path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
