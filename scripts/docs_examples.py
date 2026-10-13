"""Photo examples shown on the docs site (examples and blend-mode pages).

Each recipe's ``code`` is executed verbatim by ``scripts/build_docs.py`` to
render its preview, so the snippet on the page is always exactly the code that
produced the image. Snippets run with ``LayerImage`` and ``np`` (NumPy) in
scope and the working directory set to ``docs/``, and must leave their result
in a variable named ``image``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Photo:
    slug: str  # file name in docs/photos/ (without .jpg)
    alt: str


PHOTOS: dict[str, Photo] = {
    p.slug: p
    for p in [
        Photo("mountain-lake", "Alpine lake at sunrise with mountains reflected in the water"),
        Photo("portrait", "Older man with a grey beard and knitted cap by a workshop window"),
        Photo("city-night", "Rainy city street at night with neon reflections"),
        Photo("breakfast", "Overhead view of a breakfast table with avocado toast and berries"),
        Photo("flower-market", "Flower stall with tulips, roses, sunflowers and peonies"),
        Photo("architecture", "White building with curved balconies against a blue sky"),
        Photo("beach", "Sandy beach in late afternoon light with a lifeguard tower"),
        Photo("forest", "Misty pine forest with sun rays and ferns"),
        Photo("cafe", "Cozy cafe interior with a barista behind the counter"),
        Photo("vintage-car", "Turquoise 1960s car on a street of pastel houses"),
        Photo("harbor", "Fishing harbor on a hazy, overcast day"),
        Photo("silhouette", "Profile silhouette of a woman against a white sky"),
        Photo("snowy-cabin", "Wooden cabin in a snowy landscape with smoke from the chimney"),
    ]
}


@dataclass(frozen=True)
class Recipe:
    slug: str
    title: str
    category: str
    photo: str  # key into PHOTOS; the snippet loads it as `image`
    description: str
    code: str  # runs after `image = LayerImage.from_file("photos/<photo>.jpg")`

    @property
    def snippet(self) -> str:
        """The full snippet shown on the page and executed by the build."""
        return f'image = LayerImage.from_file("photos/{self.photo}.jpg")\n{self.code.strip()}'


CATEGORIES: list[tuple[str, str]] = [
    ("Everyday fixes", "Small corrections that make a photo look the way it felt."),
    ("Color grading", "Shift the mood of a scene with curves and color layers."),
    ("Film & vintage", "Lifted blacks, warm casts and soft contrast — the analog look."),
    ("Black & white", "Monochrome conversions, from classic to toned prints."),
    ("Creative effects", "Gradients, vignettes, double exposures and false color — "
                         "most of them mix in NumPy arrays as blend layers."),
]

RECIPES: list[Recipe] = [
    # ------------------------------------------------------------------
    # Everyday fixes
    # ------------------------------------------------------------------
    Recipe(
        slug="rescue-flat-photo",
        title="Rescue a flat photo",
        category="Everyday fixes",
        photo="harbor",
        description=(
            "A hazy, overcast shot has no true blacks or whites. Curve points "
            "computed with NumPy emulate a Levels adjustment that stretches the "
            "tones to the full range; saturation and a warm overlay bring the "
            "colors back."
        ),
        code="""
# Levels: map input 0.12 → black and 0.88 → white
x = np.linspace(0, 1, 26)
levels = np.clip((x - 0.12) / 0.76, 0, 1)

(image.curve("rgb", levels.tolist())
      .saturation(0.35)
      .overlay("#ffd8a8", opacity=0.25))
""",
    ),
    Recipe(
        slug="food-pop",
        title="Make food pop",
        category="Everyday fixes",
        photo="breakfast",
        description=(
            "Food photos benefit from rich color and a touch of warmth. A gentle "
            "S-curve adds contrast without crushing the shadows."
        ),
        code="""
(image.saturation(0.4)
      .curve("rgb", [0, 0.2, 0.52, 0.8, 1])
      .overlay("#ffc670", opacity=0.3))
""",
    ),
    Recipe(
        slug="warm-white-balance",
        title="Warm up skin tones",
        category="Everyday fixes",
        photo="portrait",
        description=(
            "Per-channel curves act as a white-balance slider: raise the red "
            "midtones and lower the blue ones to warm up a cool, grey-lit "
            "portrait."
        ),
        code="""
(image.curve("r", [0, 0.58, 1])
      .curve("b", [0, 0.43, 0.95])
      .saturation(0.1))
""",
    ),
    # ------------------------------------------------------------------
    # Color grading
    # ------------------------------------------------------------------
    Recipe(
        slug="teal-and-orange",
        title="Teal & orange",
        category="Color grading",
        photo="beach",
        description=(
            "The blockbuster grade: an S-curve on red and an inverted S-curve "
            "on blue push the shadows toward teal and the highlights toward "
            "orange."
        ),
        code="""
(image.curve("r", [0, 0.1, 0.5, 0.9, 1])
      .curve("b", [0.18, 0.38, 0.5, 0.6, 0.8])
      .contrast(1.1)
      .saturation(0.2))
""",
    ),
    Recipe(
        slug="neon-nights",
        title="Neon nights",
        category="Color grading",
        photo="city-night",
        description=(
            "Lift the blue in the shadows, wash the scene with magenta using "
            "Soft Light, and turn up saturation for a cyberpunk feel."
        ),
        code="""
(image.curve("b", [0.12, 0.45, 0.75, 1])
      .soft_light("#ff2fb3", opacity=0.6)
      .saturation(0.3)
      .contrast(1.1))
""",
    ),
    Recipe(
        slug="winter-blues",
        title="Winter blues",
        category="Color grading",
        photo="snowy-cabin",
        description=(
            "A blue Soft Light layer and a curve that lifts the blue shadows "
            "cool the whole scene; a small lightness lift keeps it airy."
        ),
        code="""
(image.soft_light("#1f5fd1", opacity=0.8)
      .curve("b", [0.1, 0.55, 1])
      .lightness(0.05))
""",
    ),
    Recipe(
        slug="moody-forest",
        title="Moody forest",
        category="Color grading",
        photo="forest",
        description=(
            "Muted greens and a deep teal cast: desaturate, crush the shadows "
            "with a curve, then multiply with a dark teal at low opacity."
        ),
        code="""
(image.saturation(-0.35)
      .curve("rgb", [0.03, 0.18, 0.45, 0.78, 0.97])
      .multiply("#2f6f6a", opacity=0.35)
      .contrast(1.15))
""",
    ),
    Recipe(
        slug="golden-glow",
        title="Golden glow",
        category="Color grading",
        photo="mountain-lake",
        description=(
            "Exaggerate the sunrise: Screen a dark orange to lift and tint the "
            "shadows, Overlay a brighter one to warm the midtones, then restore "
            "contrast with an S-curve."
        ),
        code="""
(image.screen("#3a1800", opacity=0.7)
      .overlay("#ff9d3b", opacity=0.25)
      .curve("rgb", [0, 0.18, 0.5, 0.82, 1]))
""",
    ),
    # ------------------------------------------------------------------
    # Film & vintage
    # ------------------------------------------------------------------
    Recipe(
        slug="faded-film",
        title="Faded film",
        category="Film & vintage",
        photo="cafe",
        description=(
            "Lifted blacks and softened whites give the matte look of expired "
            "film; a cream Soft Light layer warms the midtones."
        ),
        code="""
(image.curve("rgb", [0.15, 0.32, 0.55, 0.76, 0.9])
      .saturation(-0.25)
      .soft_light("#f0cf9c", opacity=0.7))
""",
    ),
    Recipe(
        slug="cross-process",
        title="Cross-processed",
        category="Film & vintage",
        photo="vintage-car",
        description=(
            "Developing slide film in negative chemistry gave punchy, yellow-"
            "green highlights and blue shadows. Opposing curves on each channel "
            "recreate it."
        ),
        code="""
(image.curve("r", [0, 0.15, 0.55, 0.9, 1])
      .curve("g", [0, 0.2, 0.55, 0.85, 1])
      .curve("b", [0.22, 0.35, 0.48, 0.6, 0.72]))
""",
    ),
    Recipe(
        slug="instant-film",
        title="Instant film",
        category="Film & vintage",
        photo="beach",
        description=(
            "Lighten with a deep navy so no shadow goes below it, warm the "
            "image with Overlay and pull back saturation for a Polaroid feel."
        ),
        code="""
(image.lighten("#2b2d4a")
      .overlay("#ffb870", opacity=0.5)
      .saturation(-0.25)
      .curve("rgb", [0, 0.27, 0.55, 0.8, 0.95]))
""",
    ),
    Recipe(
        slug="sepia",
        title="Sepia print",
        category="Film & vintage",
        photo="portrait",
        description=(
            "Convert to grayscale, then use per-channel curves as a gradient "
            "map: black becomes dark brown and white becomes warm cream."
        ),
        code="""
(image.grayscale()
      .curve("r", [0.16, 0.62, 1.0])
      .curve("g", [0.1, 0.5, 0.92])
      .curve("b", [0.06, 0.36, 0.78]))
""",
    ),
    Recipe(
        slug="lomo",
        title="Lomo",
        category="Film & vintage",
        photo="flower-market",
        description=(
            "Toy-camera look: high contrast, oversaturated color and dark "
            "corners. The vignette is a NumPy array blended with Multiply — "
            "white in the center leaves pixels untouched."
        ),
        code="""
h, w, _ = image.get_image_as_array().shape
y, x = np.ogrid[-1:1:h * 1j, -1:1:w * 1j]
vignette = np.clip(1.2 - 0.6 * (x**2 + y**2), 0, 1)[..., np.newaxis]

(image.contrast(1.3)
      .saturation(0.4)
      .multiply(vignette))
""",
    ),
    # ------------------------------------------------------------------
    # Black & white
    # ------------------------------------------------------------------
    Recipe(
        slug="classic-bw",
        title="Classic black & white",
        category="Black & white",
        photo="portrait",
        description=(
            "Grayscale alone is often flat. An S-curve restores depth and "
            "makes the textures of the beard and sweater stand out."
        ),
        code="""
(image.grayscale()
      .curve("rgb", [0, 0.15, 0.48, 0.85, 1]))
""",
    ),
    Recipe(
        slug="red-filter-bw",
        title="B&W with a red filter",
        category="Black & white",
        photo="architecture",
        description=(
            "Film photographers used a red lens filter to turn blue skies "
            "almost black. Multiplying by red before converting to grayscale "
            "does the same thing."
        ),
        code="""
(image.multiply("#ff5a36")
      .grayscale()
      .curve("rgb", [0, 0.3, 0.85, 1])
      .contrast(1.2))
""",
    ),
    Recipe(
        slug="noir",
        title="Noir",
        category="Black & white",
        photo="city-night",
        description=(
            "Crushed blacks and bright highlights for a film-noir street. The "
            "curve's low second point drives most of the frame into shadow."
        ),
        code="""
(image.grayscale()
      .curve("rgb", [0, 0.04, 0.3, 0.75, 1])
      .contrast(1.2))
""",
    ),
    Recipe(
        slug="cyanotype",
        title="Cyanotype",
        category="Black & white",
        photo="forest",
        description=(
            "The 19th-century blueprint process, recreated with a gradient map "
            "from deep Prussian blue to pale cyan."
        ),
        code="""
(image.grayscale()
      .curve("rgb", [0, 0.1, 0.55, 0.9, 1])
      .curve("r", [0.02, 0.85])
      .curve("g", [0.15, 0.95])
      .curve("b", [0.35, 1.0]))
""",
    ),
    Recipe(
        slug="high-key",
        title="High-key monochrome",
        category="Black & white",
        photo="snowy-cabin",
        description=(
            "Bright, airy black and white: lighten toward white, then add "
            "contrast so the darkest details still read."
        ),
        code="""
(image.grayscale()
      .lightness(0.3)
      .contrast(1.25))
""",
    ),
    # ------------------------------------------------------------------
    # Creative effects
    # ------------------------------------------------------------------
    Recipe(
        slug="duotone",
        title="Duotone poster",
        category="Creative effects",
        photo="architecture",
        description=(
            "Map shadows to one color and highlights to another — a two-point "
            "curve per channel is a gradient map."
        ),
        code="""
shadow, highlight = (0.12, 0.08, 0.4), (1.0, 0.45, 0.42)  # indigo → coral

image.grayscale().contrast(1.2)
for channel, lo, hi in zip("rgb", shadow, highlight):
    image.curve(channel, [lo, hi])
""",
    ),
    Recipe(
        slug="double-exposure",
        title="Double exposure",
        category="Creative effects",
        photo="silhouette",
        description=(
            "Blend modes accept another photo's pixels. Screen keeps the white "
            "sky white and fills the dark silhouette with the forest; a pale "
            "green Multiply tints the result."
        ),
        code="""
forest = LayerImage.from_file("photos/forest.jpg").get_image_as_array()

(image.screen(forest)
      .grayscale()
      .curve("rgb", [0, 0.12, 0.5, 0.88, 1])
      .multiply("#cfe3dc"))
""",
    ),
    Recipe(
        slug="graduated-filter",
        title="Graduated sky filter",
        category="Creative effects",
        photo="mountain-lake",
        description=(
            "A vertical gradient from warm tint to white, blended with Multiply, "
            "deepens the sky while leaving the lake untouched — like a "
            "graduated filter on a lens."
        ),
        code="""
h, w, _ = image.get_image_as_array().shape
t = np.clip(np.linspace(0, 2.2, h), 0, 1)[:, np.newaxis, np.newaxis]
gradient = (1 - t) * np.array([0.95, 0.55, 0.4]) + t  # tint at the top → white

image.multiply(gradient)
""",
    ),
    Recipe(
        slug="channel-swap",
        title="Channel swap",
        category="Creative effects",
        photo="vintage-car",
        description=(
            "LayerImage works on plain NumPy arrays, so anything NumPy can do is "
            "fair game. Swapping the red and green channels turns the turquoise "
            "car violet and the pink house lime."
        ),
        code="""
pixels = image.get_image_as_array()
image = LayerImage.from_array(pixels[..., [1, 0, 2]].copy())  # swap R and G

image.contrast(1.1)
""",
    ),
    Recipe(
        slug="colorize",
        title="Colorize",
        category="Creative effects",
        photo="flower-market",
        description=(
            "hue() sets every pixel to a single hue while keeping saturation "
            "and value — the whole stall becomes shades of magenta."
        ),
        code="""
image.hue(0.88).contrast(1.1)
""",
    ),
    Recipe(
        slug="pastel-dream",
        title="Pastel dream",
        category="Creative effects",
        photo="vintage-car",
        description=(
            "Soft and airy: lighten toward white, mute the colors and Screen a "
            "pale pink over everything."
        ),
        code="""
(image.lightness(0.18)
      .saturation(-0.2)
      .screen("#ffc4d6", opacity=0.35))
""",
    ),
]


# ----------------------------------------------------------------------
# Batch example: one JSON preset applied to several photos
# ----------------------------------------------------------------------

BATCH_PRESET: dict = {
    "operations": [
        {"type": "curve", "channels": "rgb", "curve_points": [0.08, 0.3, 0.55, 0.78, 0.94]},
        {"type": "saturation", "factor": -0.15},
        {"type": "soft_light", "hex": "#ffb36b", "opacity": 0.65},
        {"type": "lighten", "hex": "#1e1b2e"},
    ]
}
BATCH_PHOTOS: list[str] = ["mountain-lake", "breakfast", "harbor", "cafe"]


# ----------------------------------------------------------------------
# Blend-mode explorer
# ----------------------------------------------------------------------

BLEND_COLOR = "#e8743b"
BLEND_PHOTOS: list[str] = ["portrait", "mountain-lake", "flower-market"]

# (method, group, formula) in the order of Photoshop's blend-mode menu.
BLEND_MODES: list[tuple[str, str, str]] = [
    ("darken", "Darken", "min(A, B)"),
    ("multiply", "Darken", "A × B"),
    ("color_burn", "Darken", "1 − (1 − A) / B"),
    ("linear_burn", "Darken", "A + B − 1"),
    ("lighten", "Lighten", "max(A, B)"),
    ("screen", "Lighten", "1 − (1 − A)(1 − B)"),
    ("color_dodge", "Lighten", "A / (1 − B)"),
    ("linear_dodge", "Lighten", "A + B"),
    ("overlay", "Contrast", "2AB if A ≤ ½, else 1 − 2(1 − A)(1 − B)"),
    ("soft_light", "Contrast", "Pegtop soft light"),
    ("hard_light", "Contrast", "2AB if B ≤ ½, else 1 − 2(1 − A)(1 − B)"),
    ("vivid_light", "Contrast", "Color burn if B ≤ ½, else color dodge"),
    ("linear_light", "Contrast", "A + 2B − 1"),
    ("pin_light", "Contrast", "Replace A depending on B"),
]

OPACITY_PHOTO = "mountain-lake"
OPACITY_MODE = "overlay"
OPACITY_COLOR = "#ff4f8b"
OPACITY_STEPS: list[float] = [0.0, 0.25, 0.5, 0.75, 1.0]

COLOR_PHOTO = "portrait"
COLOR_MODE = "soft_light"
COLOR_SWATCHES: list[str] = ["#ff6b35", "#ffd23f", "#3bceac", "#0ead69", "#4361ee", "#c42bd8"]
