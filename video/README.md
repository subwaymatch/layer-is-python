# layeris video

A short walkthrough of layeris (1920×1080, 30 fps, 52.1 seconds),
built with [Remotion](https://www.remotion.dev/). The rendered file is
[`out/layeris.mp4`](out/layeris.mp4).

It follows the docs site's look: white page, DM Mono for the wordmark and
code, Schibsted Grotesk for text, Besley for section titles, and the same
syntax colors. The logo is the vector from `docs/assets/logo.svg`: its three
layers draw in fanned out, then settle into place.

| Scene | What it shows |
| --- | --- |
| Intro | The logo animation and the `layeris` wordmark |
| 01 Install | `pip install layeris`, with a quick download progress bar |
| 02 Chain operations | A chained edit, with each step's result wiping in as its line is typed |
| 03 Blend modes | All 14 blend modes applied to one photo |
| 04 Curves | Control points on the `r` and `b` channels moving, with the photo updating |
| 05 Looks | Three recipes from the docs, the last one loaded from a JSON preset |
| Outro | Install command and links |

## Every edit on screen is real

Nothing is mocked up in the browser. `scripts/build_assets.py` runs layeris
on the source photos and writes each result to `public/renders/`, along with
`src/data/assets.json`, which holds the exact code that produced each image.
The video reads its code snippets from that manifest, so the code on screen is
always the code that ran.

The source photos are the docs site's Korea-themed sample photos in
`docs/photos/`, generated with OpenAI's `gpt-image-2.5-flare` model at
`quality: low` from the prompts in the repository's
`scripts/generate_photos.py`. The video uses six of them: the hanbok
portrait, the Jeju coast, the bamboo forest, Gamcheon Culture Village, the
palace pond and the palace eaves.

## Working on it

Requires Node 18+ and, for the asset scripts, Python 3.10+ with layeris
installed from this repository (`pip install -e .` in the repo root).

```sh
cd video
npm install

npm run start     # open Remotion Studio to preview and scrub
npm run render    # render out/layeris.mp4
```

To change an edit, update `scripts/build_assets.py` and rebuild the renders:

```sh
npm run assets    # python3 scripts/build_assets.py
```

To regenerate a source photo (needs `OPENAI_API_KEY`), run the docs photo
script from the repository root, then rebuild the renders:

```sh
python3 scripts/generate_photos.py --only hanbok-portrait   # or --force for all
cd video && npm run assets
```

Scene lengths are set in each file under `src/scenes/`; the composition's
total length is their sum (see `src/Video.tsx`).

## Music

The background track, `public/music.mp3`, is a warm, minimal instrumental:
felt piano over a light beat and plucked synth arpeggios, about 99 BPM, on a
four-chord loop that changes once per bar. It was generated with the
ElevenLabs Music API (`music_v2_5`) at the video's exact length, 52.1 seconds
(1,563 frames at 30 fps). It gets fuller around the blend-modes scene and
rings out under the outro. `src/Video.tsx` mixes it in at 80% volume.

`scripts/generate_music.py` holds the prompts. To generate a new take (needs
`ELEVENLABS_API_KEY`):

```sh
python3 scripts/generate_music.py                 # "piano" style, writes public/music.mp3
python3 scripts/generate_music.py --style lofi    # or "marimba"
```

Every run gives a different take. If the video's length changes, update
`LENGTH_MS` in the script first.
