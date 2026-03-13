"""Tests for the LayerImage class."""

import json
import pathlib
from io import BytesIO

import numpy as np
from PIL import Image

from layeris import LayerImage

TEST_IMAGES_DIR = pathlib.Path(__file__).parent / "images"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def solid(value: float, channels: int = 3, size: int = 4) -> LayerImage:
    """Return a *size*×*size* image with all pixels set to *value*."""
    return LayerImage.from_array(
        np.full((size, size, channels), value, dtype=np.float64)
    )


# ---------------------------------------------------------------------------
# Factory methods
# ---------------------------------------------------------------------------


class TestFactoryMethods:
    def test_from_array_rgb(self) -> None:
        data = np.ones((5, 5, 3), dtype=np.float64) * 0.4
        img = LayerImage.from_array(data)
        np.testing.assert_array_equal(img.get_image_as_array(), data)

    def test_from_array_rgba(self) -> None:
        data = np.ones((5, 5, 4), dtype=np.float64) * 0.6
        img = LayerImage.from_array(data)
        assert img._has_alpha()

    def test_from_array_stores_float64(self) -> None:
        data = np.ones((2, 2, 3), dtype=np.float32)
        img = LayerImage.from_array(data)
        assert img.get_image_as_array().dtype == np.float64

    def test_from_file_rgb(self) -> None:
        img = LayerImage.from_file(TEST_IMAGES_DIR / "office.jpg")
        arr = img.get_image_as_array()
        assert arr.ndim == 3
        assert arr.shape[2] == 3
        assert arr.dtype == np.float64
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_from_file_string_path(self) -> None:
        img = LayerImage.from_file(str(TEST_IMAGES_DIR / "office.jpg"))
        assert img.get_image_as_array().ndim == 3


# ---------------------------------------------------------------------------
# Alpha helpers
# ---------------------------------------------------------------------------


class TestAlphaHelpers:
    def test_has_alpha_false_for_rgb(self, sample_image: LayerImage) -> None:
        assert not sample_image._has_alpha()

    def test_has_alpha_true_for_rgba(self, rgba_image: LayerImage) -> None:
        assert rgba_image._has_alpha()

    def test_get_alpha_none_for_rgb(self, sample_image: LayerImage) -> None:
        assert sample_image._get_alpha() is None

    def test_get_alpha_shape(self, rgba_image: LayerImage) -> None:
        alpha = rgba_image._get_alpha()
        assert alpha is not None
        assert alpha.shape == (4, 4, 1)

    def test_rgb_view_shape(self, rgba_image: LayerImage) -> None:
        rgb = rgba_image._rgb()
        assert rgb.shape == (4, 4, 3)

    def test_reattach_alpha_preserves_channel(self, rgba_image: LayerImage) -> None:
        original_alpha = rgba_image._get_alpha().copy()
        rgba_image.brightness(0.1)
        new_alpha = rgba_image._get_alpha()
        np.testing.assert_array_equal(new_alpha, original_alpha)


# ---------------------------------------------------------------------------
# Resize
# ---------------------------------------------------------------------------


class TestResize:
    def test_resize_changes_shape(self, office_image: LayerImage) -> None:
        office_image.resize(50, 40)
        arr = office_image.get_image_as_array()
        assert arr.shape == (40, 50, 3)

    def test_resize_values_in_range(self, office_image: LayerImage) -> None:
        office_image.resize(20, 20)
        arr = office_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_resize_returns_self(self, gray_image: LayerImage) -> None:
        result = gray_image.resize(2, 2)
        assert result is gray_image


class TestNotebookDisplay:
    def test_repr_png_returns_png_bytes(self) -> None:
        img = LayerImage.from_array(np.full((3, 4, 3), 0.5, dtype=np.float64))
        png_bytes = img._repr_png_()
        assert isinstance(png_bytes, bytes)
        assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_repr_png_preserves_image_size(self) -> None:
        img = LayerImage.from_array(np.zeros((7, 5, 3), dtype=np.float64))
        rendered = Image.open(BytesIO(img._repr_png_()))
        assert rendered.size == (5, 7)


# ---------------------------------------------------------------------------
# Adjustments
# ---------------------------------------------------------------------------


class TestGrayscale:
    def test_equal_channels(self, sample_image: LayerImage) -> None:
        sample_image.grayscale()
        arr = sample_image.get_image_as_array()
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 1])
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 2])

    def test_luminance_formula(self) -> None:
        # Single pixel: R=1, G=0, B=0  → luminance = 0.2989
        img = LayerImage.from_array(np.array([[[1.0, 0.0, 0.0]]]))
        img.grayscale()
        np.testing.assert_allclose(img.get_image_as_array()[0, 0, 0], 0.2989, atol=1e-4)

    def test_white_stays_white(self, white_image: LayerImage) -> None:
        white_image.grayscale()
        # Luminance weights sum to 0.9999, so white maps to 0.9999
        np.testing.assert_allclose(white_image.get_image_as_array(), 1.0, atol=1e-3)

    def test_black_stays_black(self, black_image: LayerImage) -> None:
        black_image.grayscale()
        np.testing.assert_allclose(black_image.get_image_as_array(), 0.0)

    def test_alpha_preserved(self, rgba_image: LayerImage) -> None:
        original_alpha = rgba_image._get_alpha().copy()
        rgba_image.grayscale()
        np.testing.assert_array_equal(rgba_image._get_alpha(), original_alpha)


class TestBrightness:
    def test_zero_factor_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.brightness(0.0)
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_positive_factor_increases(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.4))
        img.brightness(0.5)
        np.testing.assert_allclose(img.get_image_as_array(), 0.6)

    def test_clamped_to_one(self, white_image: LayerImage) -> None:
        white_image.brightness(1.0)
        np.testing.assert_allclose(white_image.get_image_as_array(), 1.0)

    def test_clamped_to_zero(self, black_image: LayerImage) -> None:
        black_image.brightness(-1.0)
        np.testing.assert_allclose(black_image.get_image_as_array(), 0.0)

    def test_returns_self(self, gray_image: LayerImage) -> None:
        assert gray_image.brightness(0.1) is gray_image


class TestContrast:
    def test_factor_one_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.contrast(1.0)
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_high_contrast_clamps_bright(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.75))
        img.contrast(2.0)
        np.testing.assert_allclose(img.get_image_as_array(), 1.0)

    def test_high_contrast_clamps_dark(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.25))
        img.contrast(2.0)
        np.testing.assert_allclose(img.get_image_as_array(), 0.0)

    def test_gray_unchanged_regardless_of_factor(self) -> None:
        # A pixel of exactly 0.5 is the pivot; contrast doesn't move it.
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.contrast(5.0)
        np.testing.assert_allclose(img.get_image_as_array(), 0.5)


class TestHue:
    def test_sets_hue_uniformly(self) -> None:
        img = LayerImage.from_file(TEST_IMAGES_DIR / "office.jpg")
        img.hue(0.5)
        arr = img.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.hue(0.3)
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0


class TestSaturation:
    def test_zero_desaturates_to_gray_tones(self, sample_image: LayerImage) -> None:
        """Removing all saturation (factor=-1) should make all channels equal."""
        sample_image.saturation(-1.0)
        arr = sample_image.get_image_as_array()
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 1], atol=1e-10)
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 2], atol=1e-10)

    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.saturation(0.5)
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0


class TestLightness:
    def test_zero_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.lightness(0.0)
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_positive_lightens(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.lightness(0.5)
        np.testing.assert_allclose(img.get_image_as_array(), 0.75)

    def test_negative_darkens(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.lightness(-0.5)
        np.testing.assert_allclose(img.get_image_as_array(), 0.25)

    def test_white_plus_positive_stays_white(self, white_image: LayerImage) -> None:
        white_image.lightness(0.5)
        np.testing.assert_allclose(white_image.get_image_as_array(), 1.0)

    def test_black_plus_negative_stays_black(self, black_image: LayerImage) -> None:
        black_image.lightness(-0.5)
        np.testing.assert_allclose(black_image.get_image_as_array(), 0.0)


class TestCurve:
    def test_identity_curve(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.curve("rgb", [0.0, 1.0])
        np.testing.assert_allclose(
            sample_image.get_image_as_array(), original, atol=1e-10
        )

    def test_default_curve_points_identity(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.curve()
        np.testing.assert_allclose(
            sample_image.get_image_as_array(), original, atol=1e-10
        )

    def test_invert_all_channels(self) -> None:
        img = LayerImage.from_array(np.full((2, 2, 3), 0.3))
        img.curve("rgb", [1.0, 0.0])
        np.testing.assert_allclose(img.get_image_as_array(), 0.7, atol=1e-10)

    def test_single_channel(self) -> None:
        data = np.ones((1, 1, 3), dtype=np.float64) * 0.5
        img = LayerImage.from_array(data)
        img.curve("r", [1.0, 0.0])
        arr = img.get_image_as_array()
        np.testing.assert_allclose(arr[0, 0, 0], 0.5, atol=1e-10)  # red inverted
        np.testing.assert_allclose(arr[0, 0, 1], 0.5)  # green unchanged
        np.testing.assert_allclose(arr[0, 0, 2], 0.5)  # blue unchanged


# ---------------------------------------------------------------------------
# Blend modes — darken group
# ---------------------------------------------------------------------------


class TestDarken:
    def test_white_darken_black(self, white_image: LayerImage) -> None:
        white_image.darken("#000000")
        np.testing.assert_allclose(white_image.get_image_as_array(), 0.0)

    def test_black_darken_white(self, black_image: LayerImage) -> None:
        black_image.darken("#ffffff")
        np.testing.assert_allclose(black_image.get_image_as_array(), 0.0)

    def test_identity_with_white(self, sample_image: LayerImage) -> None:
        """Darkening with white (#ffffff) should leave the image unchanged."""
        original = sample_image.get_image_as_array().copy()
        sample_image.darken("#ffffff")
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_opacity_blends(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.6))
        img.darken("#000000", opacity=0.5)
        # blend result = min(0.6, 0) = 0; mixed at 50%: 0.6*0.5 + 0*0.5 = 0.3
        np.testing.assert_allclose(img.get_image_as_array(), 0.3)


class TestMultiply:
    def test_multiply_by_white_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.multiply("#ffffff")
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_multiply_by_black_gives_black(self, sample_image: LayerImage) -> None:
        sample_image.multiply("#000000")
        np.testing.assert_allclose(sample_image.get_image_as_array(), 0.0)

    def test_half_times_half(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.multiply(np.array([0.5, 0.5, 0.5]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.25)


class TestColorBurn:
    def test_blend_with_white_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.color_burn("#ffffff")
        np.testing.assert_allclose(
            sample_image.get_image_as_array(), original, atol=1e-10
        )

    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.color_burn("#7fe3f8")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_known_value(self) -> None:
        # A=0.5, B=0.5 → 1 - (1-0.5)/0.5 = 1 - 1 = 0
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.color_burn(np.array([0.5, 0.5, 0.5]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.0, atol=1e-10)


class TestLinearBurn:
    def test_values_clamped(self, sample_image: LayerImage) -> None:
        sample_image.linear_burn("#e1a8ff")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_known_value(self) -> None:
        # A=0.8, B=0.8 → 0.8 + 0.8 - 1 = 0.6
        img = LayerImage.from_array(np.full((1, 1, 3), 0.8))
        img.linear_burn(np.array([0.8, 0.8, 0.8]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.6, atol=1e-10)


# ---------------------------------------------------------------------------
# Blend modes — lighten group
# ---------------------------------------------------------------------------


class TestLighten:
    def test_black_lighten_white(self, black_image: LayerImage) -> None:
        black_image.lighten("#ffffff")
        np.testing.assert_allclose(black_image.get_image_as_array(), 1.0)

    def test_white_lighten_black_no_change(self, white_image: LayerImage) -> None:
        white_image.lighten("#000000")
        np.testing.assert_allclose(white_image.get_image_as_array(), 1.0)

    def test_known_value(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.3))
        img.lighten(np.array([0.7, 0.7, 0.7]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.7)


class TestScreen:
    def test_screen_with_black_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.screen("#000000")
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_screen_with_white_gives_white(self, sample_image: LayerImage) -> None:
        sample_image.screen("#ffffff")
        np.testing.assert_allclose(sample_image.get_image_as_array(), 1.0)

    def test_known_value(self) -> None:
        # A=0.5, B=0.5 → 1 - 0.5 * 0.5 = 0.75
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.screen(np.array([0.5, 0.5, 0.5]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.75)


class TestColorDodge:
    def test_blend_with_black_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.color_dodge("#000000")
        np.testing.assert_allclose(
            sample_image.get_image_as_array(), original, atol=1e-10
        )

    def test_blend_with_white_gives_white(self, sample_image: LayerImage) -> None:
        sample_image.color_dodge("#ffffff")
        np.testing.assert_allclose(sample_image.get_image_as_array(), 1.0)

    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.color_dodge("#490cc7")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0


class TestLinearDodge:
    def test_clamps_to_one(self, white_image: LayerImage) -> None:
        white_image.linear_dodge("#ffffff")
        np.testing.assert_allclose(white_image.get_image_as_array(), 1.0)

    def test_blend_with_black_no_change(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.linear_dodge("#000000")
        np.testing.assert_allclose(sample_image.get_image_as_array(), original)

    def test_known_value(self) -> None:
        # A=0.5, B=0.5 → clamped(1.0) = 1.0
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.linear_dodge(np.array([0.5, 0.5, 0.5]))
        np.testing.assert_allclose(img.get_image_as_array(), 1.0)


# ---------------------------------------------------------------------------
# Blend modes — contrast group
# ---------------------------------------------------------------------------


class TestOverlay:
    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.overlay("#ffb956")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_dark_base_uses_multiply_branch(self) -> None:
        # A=0.2, B=0.3, A<=0.5 → 2*0.2*0.3 = 0.12
        img = LayerImage.from_array(np.full((1, 1, 3), 0.2))
        img.overlay(np.array([0.3, 0.3, 0.3]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.12, atol=1e-10)

    def test_light_base_uses_screen_branch(self) -> None:
        # A=0.8, B=0.3, A>0.5 → 1 - 2*(1-0.8)*(1-0.3) = 1 - 2*0.2*0.7 = 0.72
        img = LayerImage.from_array(np.full((1, 1, 3), 0.8))
        img.overlay(np.array([0.3, 0.3, 0.3]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.72, atol=1e-10)


class TestSoftLight:
    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.soft_light("#ff3cbc")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_gray_on_gray_unchanged(self) -> None:
        # A=0.5, B=0.5: data01 = 2*0.5*0.5 + 0.25*(1-1) = 0.5
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.soft_light(np.array([0.5, 0.5, 0.5]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.5, atol=1e-10)


class TestHardLight:
    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.hard_light("#df5dff")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_dark_blend_uses_multiply_branch(self) -> None:
        # A=0.5, B=0.3, B<=0.5 → 2*0.5*0.3 = 0.3
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.hard_light(np.array([0.3, 0.3, 0.3]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.3, atol=1e-10)


class TestVividLight:
    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.vivid_light("#ac5b7f")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0


class TestLinearLight:
    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.linear_light("#9fa500")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_known_value(self) -> None:
        # A=0.5, B=0.3 → 0.5 + 2*0.3 - 1 = 0.1
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.linear_light(np.array([0.3, 0.3, 0.3]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.1, atol=1e-10)


class TestPinLight:
    def test_values_in_range(self, sample_image: LayerImage) -> None:
        sample_image.pin_light("#005546")
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_a_between_bounds_returns_a(self) -> None:
        # A=0.5, B=0.3: 2B-1=-0.4, 2B=0.6; A not < -0.4 and not > 0.6 → result = A
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.pin_light(np.array([0.3, 0.3, 0.3]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.5, atol=1e-10)

    def test_a_above_upper_bound(self) -> None:
        # A=0.8, B=0.3: 2B=0.6; A > 0.6 → result = 2B = 0.6
        img = LayerImage.from_array(np.full((1, 1, 3), 0.8))
        img.pin_light(np.array([0.3, 0.3, 0.3]))
        np.testing.assert_allclose(img.get_image_as_array(), 0.6, atol=1e-10)


# ---------------------------------------------------------------------------
# Utility methods
# ---------------------------------------------------------------------------


class TestClone:
    def test_clone_is_independent(self, sample_image: LayerImage) -> None:
        clone = sample_image.clone()
        original_data = sample_image.get_image_as_array().copy()
        clone.brightness(0.5)
        np.testing.assert_allclose(sample_image.get_image_as_array(), original_data)

    def test_clone_has_same_values(self, sample_image: LayerImage) -> None:
        clone = sample_image.clone()
        np.testing.assert_array_equal(
            clone.get_image_as_array(), sample_image.get_image_as_array()
        )


class TestGetImageAsArray:
    def test_returns_float64(self, sample_image: LayerImage) -> None:
        assert sample_image.get_image_as_array().dtype == np.float64

    def test_shape_rgb(self, sample_image: LayerImage) -> None:
        arr = sample_image.get_image_as_array()
        assert arr.ndim == 3
        assert arr.shape[2] == 3


# ---------------------------------------------------------------------------
# Method chaining
# ---------------------------------------------------------------------------


class TestMethodChaining:
    def test_chain_returns_self(self, sample_image: LayerImage) -> None:
        result = (
            sample_image.grayscale().brightness(0.1).contrast(1.1).multiply("#aaaaaa")
        )
        assert result is sample_image

    def test_chain_produces_valid_output(self, office_image: LayerImage) -> None:
        office_image.grayscale().brightness(0.2).screen("#3fe28f")
        arr = office_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0


# ---------------------------------------------------------------------------
# apply_from_dict / apply_from_json
# ---------------------------------------------------------------------------


class TestApplyFromDict:
    def test_grayscale_op(self, sample_image: LayerImage) -> None:
        sample_image.apply_from_dict({"operations": [{"type": "grayscale"}]})
        arr = sample_image.get_image_as_array()
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 1])

    def test_brightness_op(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.4))
        img.apply_from_dict({"operations": [{"type": "brightness", "factor": 0.5}]})
        np.testing.assert_allclose(img.get_image_as_array(), 0.6)

    def test_contrast_op(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.apply_from_dict({"operations": [{"type": "contrast", "factor": 2.0}]})
        np.testing.assert_allclose(img.get_image_as_array(), 0.5)

    def test_lightness_op(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.apply_from_dict({"operations": [{"type": "lightness", "factor": 0.5}]})
        np.testing.assert_allclose(img.get_image_as_array(), 0.75)

    def test_saturation_op(self, sample_image: LayerImage) -> None:
        sample_image.apply_from_dict(
            {"operations": [{"type": "saturation", "factor": -1.0}]}
        )
        arr = sample_image.get_image_as_array()
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 1], atol=1e-10)

    def test_hue_op(self, sample_image: LayerImage) -> None:
        sample_image.apply_from_dict({"operations": [{"type": "hue", "hue": 0.5}]})
        arr = sample_image.get_image_as_array()
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_curve_op(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.apply_from_dict(
            {
                "operations": [
                    {"type": "curve", "channels": "rgb", "curve_points": [0, 1]}
                ]
            }
        )
        np.testing.assert_allclose(
            sample_image.get_image_as_array(), original, atol=1e-10
        )

    def test_resize_op(self, office_image: LayerImage) -> None:
        office_image.apply_from_dict(
            {"operations": [{"type": "resize", "width": 30, "height": 20}]}
        )
        assert office_image.get_image_as_array().shape == (20, 30, 3)

    def test_blend_mode_op_multiply(self) -> None:
        img = LayerImage.from_array(np.full((1, 1, 3), 0.5))
        img.apply_from_dict(
            {"operations": [{"type": "multiply", "hex": "#ffffff", "opacity": 1.0}]}
        )
        np.testing.assert_allclose(img.get_image_as_array(), 0.5)

    def test_all_blend_modes_via_dict(self, sample_image: LayerImage) -> None:
        blend_modes = [
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
        for mode in blend_modes:
            clone = sample_image.clone()
            clone.apply_from_dict(
                {"operations": [{"type": mode, "hex": "#808080", "opacity": 0.5}]}
            )
            arr = clone.get_image_as_array()
            assert arr.min() >= 0.0, f"{mode} produced value < 0"
            assert arr.max() <= 1.0, f"{mode} produced value > 1"

    def test_unknown_op_ignored(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.apply_from_dict({"operations": [{"type": "unknown_operation"}]})
        np.testing.assert_array_equal(sample_image.get_image_as_array(), original)

    def test_empty_operations(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.apply_from_dict({"operations": []})
        np.testing.assert_array_equal(sample_image.get_image_as_array(), original)

    def test_missing_factor_ignored(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        # brightness without factor should be silently ignored
        sample_image.apply_from_dict({"operations": [{"type": "brightness"}]})
        np.testing.assert_array_equal(sample_image.get_image_as_array(), original)

    def test_blend_mode_without_hex_ignored(self, sample_image: LayerImage) -> None:
        original = sample_image.get_image_as_array().copy()
        sample_image.apply_from_dict({"operations": [{"type": "multiply"}]})
        np.testing.assert_array_equal(sample_image.get_image_as_array(), original)

    def test_returns_self(self, sample_image: LayerImage) -> None:
        result = sample_image.apply_from_dict({"operations": []})
        assert result is sample_image


class TestApplyFromJson:
    def test_apply_from_json(
        self, tmp_path: pathlib.Path, sample_image: LayerImage
    ) -> None:
        ops = {
            "operations": [{"type": "grayscale"}, {"type": "brightness", "factor": 0.1}]
        }
        json_file = tmp_path / "ops.json"
        json_file.write_text(json.dumps(ops))
        sample_image.apply_from_json(json_file)
        arr = sample_image.get_image_as_array()
        np.testing.assert_allclose(arr[:, :, 0], arr[:, :, 1])

    def test_returns_self(
        self, tmp_path: pathlib.Path, sample_image: LayerImage
    ) -> None:
        json_file = tmp_path / "empty.json"
        json_file.write_text(json.dumps({"operations": []}))
        result = sample_image.apply_from_json(json_file)
        assert result is sample_image


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------


class TestSave:
    def test_save_jpeg(self, tmp_path: pathlib.Path, office_image: LayerImage) -> None:
        out = tmp_path / "output.jpg"
        office_image.save(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_save_png(self, tmp_path: pathlib.Path, sample_image: LayerImage) -> None:
        out = tmp_path / "output.png"
        sample_image.save(out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_save_jpeg_rgba_composites_to_white(
        self, tmp_path: pathlib.Path, rgba_image: LayerImage
    ) -> None:
        out = tmp_path / "output.jpg"
        rgba_image.save(out)
        assert out.exists()

    def test_save_returns_self(
        self, tmp_path: pathlib.Path, sample_image: LayerImage
    ) -> None:
        result = sample_image.save(tmp_path / "out.jpg")
        assert result is sample_image

    def test_save_and_reload_roundtrip(
        self, tmp_path: pathlib.Path, office_image: LayerImage
    ) -> None:
        out = tmp_path / "roundtrip.png"
        original_shape = office_image.get_image_as_array().shape
        office_image.save(out)
        reloaded = LayerImage.from_file(out)
        assert reloaded.get_image_as_array().shape == original_shape
