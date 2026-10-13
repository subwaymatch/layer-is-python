"""The 8-bit lookup-table path must match the float64 path pixel for pixel.

Photos loaded with ``from_file`` keep their 8-bit pixels and fold per-channel
operations into a lookup table. ``float_path`` loads the same pixels through
``from_array``, which processes every pixel in float64, and serves as the
reference.
"""

import pathlib
from collections.abc import Callable

import numpy as np
import pytest
from PIL import Image

from layeris import LayerImage

TEST_IMAGES_DIR = pathlib.Path(__file__).parent / "images"

BLEND_MODES = [
    "darken",
    "multiply",
    "color_burn",
    "linear_burn",
    "lighten",
    "screen",
    "color_dodge",
    "linear_dodge",
    "overlay",
    "soft_light",
    "hard_light",
    "vivid_light",
    "linear_light",
    "pin_light",
]

Op = Callable[[LayerImage], LayerImage]

PER_CHANNEL_OPS: dict[str, Op] = {
    "brightness up": lambda img: img.brightness(0.3),
    "brightness down": lambda img: img.brightness(-0.4),
    "contrast": lambda img: img.contrast(1.6),
    "lightness up": lambda img: img.lightness(0.4),
    "lightness down": lambda img: img.lightness(-0.5),
    "lightness zero": lambda img: img.lightness(0),
    "curve rgb": lambda img: img.curve("rgb", [0, 0.1, 0.4, 0.65, 0.9, 1]),
    "curve two channels": lambda img: img.curve("gb", [0.2, 0.9]),
    "curve default": lambda img: img.curve(),
    "uniform array blend": lambda img: img.overlay(np.array([0.9, 0.3, 0.5])),
    **{
        f"{mode} with opacity": (
            lambda mode: lambda img: getattr(img, mode)("#3fe28f", opacity=0.6)
        )(mode)
        for mode in BLEND_MODES
    },
    **{
        f"{mode} with white and black": (
            lambda mode: lambda img: getattr(getattr(img, mode)("#fff"), mode)("#000")
        )(mode)
        for mode in BLEND_MODES
    },
}


def _gradient(img: LayerImage) -> np.ndarray:
    height = img.get_image_as_array().shape[0]
    return np.linspace(0, 1, height)[:, None, None] * np.array([1.0, 0.6, 0.3]) + 0.2


MIXED_CHAINS: dict[str, Op] = {
    "grayscale first": lambda img: (
        img.grayscale()
        .brightness(0.1)
        .multiply("#3fe28f", opacity=0.7)
        .curve("rgb", [0, 0.1, 0.4, 0.65, 0.9, 1])
    ),
    "table then grayscale": lambda img: (
        img.curve("r", [0, 0.8, 1]).screen("#223344").grayscale().contrast(1.3)
    ),
    "hue and saturation": lambda img: (
        img.contrast(1.2).saturation(0.4).brightness(-0.1).hue(0.6).soft_light("#f0a")
    ),
    "per-pixel array blend": lambda img: (
        img.brightness(0.1).multiply(_gradient(img)).contrast(1.2)
    ),
    "resize between tables": lambda img: (
        img.contrast(1.3).resize(41, 29).brightness(0.2)
    ),
    "operations from a dict": lambda img: img.apply_from_dict(
        {
            "operations": [
                {"type": "curve", "channels": "rgb", "curve_points": [0.1, 0.5, 0.9]},
                {"type": "saturation", "factor": -0.15},
                {"type": "soft_light", "hex": "#ffb36b", "opacity": 0.65},
                {"type": "lighten", "hex": "#1e1b2e"},
            ]
        }
    ),
}


@pytest.fixture(params=["RGB", "RGBA"])
def photo(request: pytest.FixtureRequest, tmp_path: pathlib.Path) -> pathlib.Path:
    """A small real photo saved as PNG, with metadata, in RGB or RGBA."""
    image = Image.open(TEST_IMAGES_DIR / "office.jpg").convert("RGB").resize((64, 48))
    if request.param == "RGBA":
        pixels = np.asarray(image.convert("RGBA")).copy()
        pixels[:, :, 3] = np.linspace(0, 255, 64, dtype=np.uint8)[None, :]
        image = Image.fromarray(pixels, "RGBA")
    path = tmp_path / f"photo-{request.param}.png"
    image.save(path, dpi=(300, 300))
    return path


def float_path(path: pathlib.Path) -> LayerImage:
    """The same photo, processed per pixel in float64."""
    with Image.open(path) as image:
        return LayerImage.from_array(np.asarray(image) / 255)


def assert_same_pixels(fast: LayerImage, reference: LayerImage) -> None:
    fast_pixels = fast.get_image_as_array()
    assert fast_pixels.dtype == np.float64
    np.testing.assert_array_equal(fast_pixels, reference.get_image_as_array())


class TestLookupTablePath:
    @pytest.mark.parametrize("op", PER_CHANNEL_OPS.values(), ids=PER_CHANNEL_OPS.keys())
    def test_per_channel_op_matches_float_path(
        self, photo: pathlib.Path, op: Op
    ) -> None:
        assert_same_pixels(op(LayerImage.from_file(photo)), op(float_path(photo)))

    @pytest.mark.parametrize("op", MIXED_CHAINS.values(), ids=MIXED_CHAINS.keys())
    def test_mixed_chain_matches_float_path(self, photo: pathlib.Path, op: Op) -> None:
        assert_same_pixels(op(LayerImage.from_file(photo)), op(float_path(photo)))

    @pytest.mark.parametrize("ext", ["png", "jpg"])
    @pytest.mark.parametrize("op", MIXED_CHAINS.values(), ids=MIXED_CHAINS.keys())
    def test_saved_file_matches_float_path(
        self, photo: pathlib.Path, tmp_path: pathlib.Path, op: Op, ext: str
    ) -> None:
        fast_file, reference_file = tmp_path / f"fast.{ext}", tmp_path / f"ref.{ext}"
        op(LayerImage.from_file(photo).brightness(0.1)).save(fast_file)
        op(float_path(photo).brightness(0.1)).save(reference_file)
        assert fast_file.read_bytes() == reference_file.read_bytes()

    def test_png_repr_matches_float_path(self, photo: pathlib.Path) -> None:
        fast = LayerImage.from_file(photo).overlay("#ffcc00").contrast(1.2)
        reference = float_path(photo).overlay("#ffcc00").contrast(1.2)
        assert fast._repr_png_() == reference._repr_png_()

    def test_per_channel_ops_are_deferred(self, photo: pathlib.Path) -> None:
        img = LayerImage.from_file(photo).brightness(0.2).curve("r", [0, 0.7, 1])
        img.multiply("#3fe28f", opacity=0.5)
        assert img._data is None, "per-channel ops should not touch float pixels"
        assert img._lut is not None and img._lut.shape == (1, 256, 3)

    def test_resize_keeps_8bit_pixels(self, photo: pathlib.Path) -> None:
        img = LayerImage.from_file(photo).contrast(1.3).resize(20, 10)
        assert img._data is None
        assert repr(img).endswith(" 20x10>")

    def test_get_image_as_array_returns_live_array(self, photo: pathlib.Path) -> None:
        img = LayerImage.from_file(photo).brightness(0.2)
        pixels = img.get_image_as_array()
        assert img.get_image_as_array() is pixels
        pixels[:, :, :3] = 0.25
        img.brightness(1.0)
        np.testing.assert_allclose(img.get_image_as_array()[:, :, :3], 0.5)

    def test_clone_is_independent(self, photo: pathlib.Path) -> None:
        img = LayerImage.from_file(photo).brightness(0.2)
        twin = img.clone().contrast(2.0)
        assert_same_pixels(img, float_path(photo).brightness(0.2))
        assert_same_pixels(twin, float_path(photo).brightness(0.2).contrast(2.0))

    def test_repr_matches_float_path(self, photo: pathlib.Path) -> None:
        assert repr(LayerImage.from_file(photo)) == repr(float_path(photo))

    def test_invalid_arguments_raise_immediately(self, photo: pathlib.Path) -> None:
        img = LayerImage.from_file(photo)
        with pytest.raises(ValueError, match="opacity"):
            img.multiply("#ffffff", opacity=1.5)
        with pytest.raises(ValueError, match="channels"):
            img.curve("x", [0, 1])
        with pytest.raises(ValueError, match="control points"):
            img.curve("r", [0.5])
        with pytest.raises(ValueError, match="hex"):
            img.screen("not a colour")
