"""API reference content for the docs site (``docs/api.html``).

Written by hand from ``src/layeris/layer_image.py``. ``scripts/build_docs.py``
checks that every public ``LayerImage`` method is covered here (blend modes
through the shared ``blend_mode`` entry), so a new method cannot be left out.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Param:
    name: str
    type: str
    description: str


@dataclass(frozen=True)
class Entry:
    name: str  # method name, also the anchor id
    prefix: str  # "LayerImage." for constructors, "image." for methods
    args: str  # the signature as shown, including parentheses
    description: str
    params: list[Param] = field(default_factory=list)
    returns: str = "LayerImage"
    returns_note: str = "(the same image)"
    raises: list[tuple[str, str]] = field(default_factory=list)  # (exception, when)
    code: str = ""
    see: tuple[str, str] | None = None  # (href, label)
    lists_blend_modes: bool = False


@dataclass(frozen=True)
class Group:
    id: str
    title: str
    entries: list[Entry]
    intro: str = ""


def _before_after(slug: str) -> tuple[str, str]:
    return (f"operations.html#{slug}", "Before and after")


DICT_SAMPLE = """image.apply_from_dict({
    "operations": [
        {"type": "grayscale"},
        {"type": "brightness", "factor": 0.2},
        {"type": "multiply", "hex": "#ff0000", "opacity": 0.5},
        {"type": "resize", "width": 800, "height": 600},
        {"type": "curve", "channels": "rgb", "curve_points": [0, 0.5, 1]},
    ]
})"""

GROUPS: list[Group] = [
    Group("creating", "Creating an Image", [
        Entry(
            "from_file", "LayerImage.", "(file_path)",
            "Open an image file with Pillow. EXIF orientation is applied, so photos from "
            "cameras and phones load upright. Any color mode is converted to RGB, or to RGBA "
            "when the image has transparency. Metadata such as EXIF data and ICC profiles is "
            "not kept.",
            [Param("file_path", "str | Path", "Path to any image file Pillow can open.")],
            returns_note="",
        ),
        Entry(
            "from_url", "LayerImage.", "(url, timeout=30.0)",
            "Download an image over HTTP(S) with Requests, then open it the same way as "
            "from_file().",
            [
                Param("url", "str", "Address of the image."),
                Param("timeout", "float = 30.0", "Seconds to wait for the server."),
            ],
            returns_note="",
            raises=[("requests.HTTPError", "when the server responds with an error status")],
        ),
        Entry(
            "from_array", "LayerImage.", "(image_data)",
            "Wrap a NumPy array of floats with values in [0, 1].",
            [Param("image_data", "NDArray[float64]",
                   "Shape (height, width, 3) for RGB or (height, width, 4) for RGBA.")],
            returns_note="",
            raises=[
                ("TypeError", "for an array that is not float (divide 8-bit data by 255 first)"),
                ("ValueError", "for any other shape"),
            ],
        ),
    ]),
    Group("output", "Saving and Output", [
        Entry(
            "save", "image.", "(filename, quality=95)",
            "Write the image to a file. The format comes from the file extension: JPEG, PNG, "
            "BMP, TIFF, WebP or any other format Pillow can write. An RGBA image saved as JPEG "
            "is composited onto a white background.",
            [
                Param("filename", "str | Path", "Output path."),
                Param("quality", "int = 95", "JPEG quality from 0 to 100. Other formats ignore it."),
            ],
        ),
        Entry(
            "get_image_as_array", "image.", "()",
            "Return the pixels as a float64 array with values in [0, 1] and shape "
            "(height, width, 3) or (height, width, 4). This is the underlying array, not a "
            "copy. For a photo loaded from a file or URL, it applies any pending per-channel "
            "operations and keeps the image in float64 from then on.",
            returns="NDArray[float64]",
            returns_note="",
            see=("index.html#performance", "Performance"),
        ),
        Entry(
            "clone", "image.", "()",
            "Return an independent copy, including any operations still pending in the "
            "lookup table. Changes to the copy do not affect the original.",
            returns_note="(a new image)",
        ),
    ], intro="In a Jupyter notebook, a LayerImage displays as the image itself. Its repr "
             "shows the mode and size, for example <LayerImage RGB 1536x1024>."),
    Group("adjustments", "Adjustments", [
        Entry(
            "grayscale", "image.", "()",
            "Convert to grayscale with the ITU-R 601 luminance weights (0.2989, 0.5870, "
            "0.1140). The alpha channel is kept.",
            see=_before_after("grayscale"),
        ),
        Entry(
            "brightness", "image.", "(factor)",
            "Multiply every channel by 1 + factor and clip to [0, 1]. A factor above 0 "
            "brightens, below 0 darkens.",
            [Param("factor", "float", "0 leaves the image unchanged.")],
            see=_before_after("brightness"),
        ),
        Entry(
            "contrast", "image.", "(factor)",
            "Scale each value around mid-gray, factor * (value - 0.5) + 0.5, and clip to "
            "[0, 1]. Above 1 increases contrast; between 0 and 1 decreases it.",
            [Param("factor", "float", "1 leaves the image unchanged.")],
            see=_before_after("contrast"),
        ),
        Entry(
            "hue", "image.", "(target_hue)",
            "Set every pixel's hue to target_hue while keeping saturation and value. This is "
            "a colorize-style adjustment.",
            [Param("target_hue", "float", "Hue in [0, 1].")],
            see=_before_after("hue"),
        ),
        Entry(
            "saturation", "image.", "(factor)",
            "Multiply saturation by 1 + factor and clip to [0, 1]. Above 0 boosts color, "
            "below 0 mutes it.",
            [Param("factor", "float", "-1 removes all color. 0 leaves the image unchanged.")],
            see=_before_after("saturation"),
        ),
        Entry(
            "lightness", "image.", "(factor)",
            "Blend toward white when factor is above 0, or toward black when it is below 0.",
            [Param("factor", "float", "From -1 (black) to 1 (white). 0 leaves the image "
                                      "unchanged.")],
            see=_before_after("lightness"),
        ),
        Entry(
            "curve", "image.", '(channels="rgb", curve_points=None)',
            "Remap tones through control points spaced evenly across [0, 1], on any "
            "combination of the red, green and blue channels.",
            [
                Param("channels", 'str = "rgb"', 'Any non-empty combination of r, g and b, '
                                                 'such as "rgb", "r" or "gb".'),
                Param("curve_points", "list[float] | None = None",
                      "Output levels in [0, 1]. The default, [0, 1], leaves the image "
                      "unchanged."),
            ],
            raises=[("ValueError", "for any other channel letters")],
            see=_before_after("curve_rgb"),
        ),
        Entry(
            "resize", "image.", "(width, height)",
            "Resize with Lanczos resampling. A photo loaded from a file or URL stays 8-bit.",
            [
                Param("width", "int", "New width in pixels, at least 1."),
                Param("height", "int", "New height in pixels, at least 1."),
            ],
            raises=[("ValueError", "if width or height is below 1")],
            see=_before_after("resize"),
        ),
    ]),
    Group("blending", "Blend Modes", [
        Entry(
            "blend_mode", "image.", "(blend_data, opacity=1.0)",
            "Every blend mode has this signature: replace blend_mode with one of the "
            "{count} methods below. Each combines the image (the base, A) with a blend layer "
            "(B), then mixes the result back with the original by opacity. A hex color, or an "
            "array with one value per channel, keeps an 8-bit photo on the lookup-table path. "
            "A per-pixel array converts it to float64 first.",
            [
                Param("blend_data", "str | NDArray[float64]",
                      'A hex color such as "#e8743b", or a float array in [0, 1] that '
                      "broadcasts to the image: shape (3,) for one color, or "
                      "(height, width, 3) for a per-pixel layer such as a gradient or "
                      "another photo."),
                Param("opacity", "float = 1.0", "From 0 (no change) to 1 (full effect)."),
            ],
            see=("blend-modes.html", "All {count} modes compared"),
            lists_blend_modes=True,
        ),
    ]),
    Group("data", "Operations as Data", [
        Entry(
            "apply_from_dict", "image.", "(data)",
            "Run a sequence of operations described in a dictionary, in order. The operation "
            "types below list the keys each one takes.",
            [Param("data", "dict", 'A dict with an "operations" list.')],
            code=DICT_SAMPLE,
            see=("#json-types", "Operation types"),
        ),
        Entry(
            "apply_from_json", "image.", "(filepath)",
            "Load a JSON file with the same structure and pass it to apply_from_dict().",
            [Param("filepath", "str | Path", "Path to the JSON file.")],
            code='image.apply_from_json("pipeline.json")',
            see=("examples.html#batch", "Batch example"),
        ),
    ]),
]

# (type, keys, call) for each entry of the "operations" list.
JSON_TYPES: list[tuple[str, str, str]] = [
    ("grayscale", "none", "grayscale()"),
    ("brightness", "factor", "brightness(factor)"),
    ("contrast", "factor", "contrast(factor)"),
    ("saturation", "factor", "saturation(factor)"),
    ("lightness", "factor", "lightness(factor)"),
    ("hue", "hue", "hue(hue)"),
    ("curve", "channels, curve_points", "curve(channels, curve_points)"),
    ("resize", "width, height", "resize(width, height)"),
    ("any blend mode, such as multiply", "hex, opacity (optional, default 1.0)",
     "multiply(hex, opacity)"),
]
