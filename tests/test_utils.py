"""Tests for layeris utility modules."""

import numpy as np
import pytest

from layeris.utils.channels import channel_adjust, merge_channels, split_image_into_channels
from layeris.utils.conversions import (
    get_array_from_hex,
    get_rgb_float_if_hex,
    hex_to_rgb,
    hex_to_rgb_float,
    convert_float_to_uint,
    convert_uint_to_float,
    round_to_uint,
)
from layeris.utils.hsl import hsl_to_rgb, hsl_to_rgb_arr, rgb_to_hsl, rgb_to_hsl_arr
from layeris.utils.layers import mix


# ---------------------------------------------------------------------------
# layeris.utils.conversions
# ---------------------------------------------------------------------------


class TestConvertUintToFloat:
    def test_zero(self) -> None:
        data = np.zeros((2, 2, 3), dtype=np.uint8)
        result = convert_uint_to_float(data)
        assert result.shape == (2, 2, 3)
        assert np.all(result == 0.0)

    def test_max_value(self) -> None:
        data = np.full((1, 1, 3), 255, dtype=np.uint8)
        result = convert_uint_to_float(data)
        np.testing.assert_allclose(result, 1.0)

    def test_midpoint(self) -> None:
        data = np.array([[[128]], [[0]]], dtype=np.uint8)
        result = convert_uint_to_float(data)
        np.testing.assert_allclose(result[0, 0, 0], 128 / 255)


class TestConvertFloatToUint:
    def test_zero(self) -> None:
        data = np.zeros((2, 2, 3), dtype=np.float64)
        result = convert_float_to_uint(data)
        assert result.dtype == np.uint8
        assert np.all(result == 0)

    def test_one(self) -> None:
        data = np.ones((2, 2, 3), dtype=np.float64)
        result = convert_float_to_uint(data)
        assert np.all(result == 255)

    def test_roundtrip(self) -> None:
        original = np.array([[[100, 150, 200]]], dtype=np.uint8)
        result = convert_float_to_uint(convert_uint_to_float(original))
        np.testing.assert_array_equal(result, original)


class TestRoundToUint:
    def test_rounding(self) -> None:
        data = np.array([0.4, 0.5, 0.6])
        result = round_to_uint(data)
        assert result.dtype == np.uint8
        np.testing.assert_array_equal(result, [0, 0, 1])


class TestHexConversions:
    def test_hex_to_rgb_red(self) -> None:
        result = hex_to_rgb("#ff0000")
        np.testing.assert_array_equal(result, [255, 0, 0])

    def test_hex_to_rgb_white(self) -> None:
        result = hex_to_rgb("#ffffff")
        np.testing.assert_array_equal(result, [255, 255, 255])

    def test_hex_to_rgb_black(self) -> None:
        result = hex_to_rgb("#000000")
        np.testing.assert_array_equal(result, [0, 0, 0])

    def test_hex_to_rgb_float_red(self) -> None:
        result = hex_to_rgb_float("#ff0000")
        np.testing.assert_allclose(result, [1.0, 0.0, 0.0])

    def test_hex_to_rgb_float_white(self) -> None:
        result = hex_to_rgb_float("#ffffff")
        np.testing.assert_allclose(result, [1.0, 1.0, 1.0])

    def test_hex_to_rgb_no_hash(self) -> None:
        result = hex_to_rgb("00ff00")
        np.testing.assert_array_equal(result, [0, 255, 0])

    def test_get_rgb_float_if_hex_string(self) -> None:
        result = get_rgb_float_if_hex("#ff0000")
        np.testing.assert_allclose(result, [1.0, 0.0, 0.0])

    def test_get_rgb_float_if_hex_array(self) -> None:
        arr = np.array([0.5, 0.5, 0.5])
        result = get_rgb_float_if_hex(arr)
        np.testing.assert_array_equal(result, arr)

    def test_get_array_from_hex(self) -> None:
        result = get_array_from_hex("#ff0000", 3, 4)
        assert result.shape == (3, 4, 3)
        np.testing.assert_allclose(result[0, 0], [1.0, 0.0, 0.0])


# ---------------------------------------------------------------------------
# layeris.utils.channels
# ---------------------------------------------------------------------------


class TestChannels:
    def setup_method(self) -> None:
        # 2×2 RGB image
        self.image = np.array(
            [[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]], [[0.7, 0.8, 0.9], [1.0, 0.0, 0.5]]],
            dtype=np.float64,
        )

    def test_split_shapes(self) -> None:
        r, g, b = split_image_into_channels(self.image)
        assert r.shape == (2, 2)
        assert g.shape == (2, 2)
        assert b.shape == (2, 2)

    def test_split_values(self) -> None:
        r, g, b = split_image_into_channels(self.image)
        np.testing.assert_allclose(r, self.image[:, :, 0])
        np.testing.assert_allclose(g, self.image[:, :, 1])
        np.testing.assert_allclose(b, self.image[:, :, 2])

    def test_merge_roundtrip(self) -> None:
        r, g, b = split_image_into_channels(self.image)
        reconstructed = merge_channels(r, g, b)
        np.testing.assert_allclose(reconstructed, self.image)

    def test_channel_adjust_identity(self) -> None:
        r, _, _ = split_image_into_channels(self.image)
        result = channel_adjust(r, [0.0, 1.0])
        np.testing.assert_allclose(result, r, atol=1e-10)

    def test_channel_adjust_invert(self) -> None:
        r, _, _ = split_image_into_channels(self.image)
        inverted = channel_adjust(r, [1.0, 0.0])
        np.testing.assert_allclose(inverted, 1.0 - r, atol=1e-10)

    def test_channel_adjust_clamp_bright(self) -> None:
        """Mapping [0, 2] scales values up (clamped by consumers)."""
        channel = np.array([[0.5, 1.0]])
        result = channel_adjust(channel, [0.0, 2.0])
        np.testing.assert_allclose(result[0, 0], 1.0)


# ---------------------------------------------------------------------------
# layeris.utils.layers
# ---------------------------------------------------------------------------


class TestMix:
    def test_full_opacity(self) -> None:
        base = np.array([0.0, 0.0, 0.0])
        blend = np.array([1.0, 1.0, 1.0])
        result = mix(base, blend, 1.0)
        np.testing.assert_array_equal(result, blend)

    def test_zero_opacity(self) -> None:
        base = np.array([0.2, 0.4, 0.6])
        blend = np.array([1.0, 1.0, 1.0])
        result = mix(base, blend, 0.0)
        np.testing.assert_allclose(result, base)

    def test_half_opacity(self) -> None:
        base = np.array([0.0, 0.0, 0.0])
        blend = np.array([1.0, 1.0, 1.0])
        result = mix(base, blend, 0.5)
        np.testing.assert_allclose(result, [0.5, 0.5, 0.5])


# ---------------------------------------------------------------------------
# layeris.utils.hsl
# ---------------------------------------------------------------------------


class TestHslConversions:
    def test_rgb_to_hsl_red(self) -> None:
        # Pure red in HSL: hue ~0, saturation 1, lightness 0.5
        hsl = rgb_to_hsl(np.array([1.0, 0.0, 0.0]))
        assert abs(hsl[0]) < 1e-6 or abs(hsl[0] - 1.0) < 1e-6  # hue wraps
        assert abs(hsl[1] - 1.0) < 1e-6

    def test_rgb_to_hsl_gray(self) -> None:
        # Mid-grey: saturation should be 0
        hsl = rgb_to_hsl(np.array([0.5, 0.5, 0.5]))
        assert abs(hsl[1]) < 1e-6

    def test_hsl_to_rgb_gray(self) -> None:
        rgb = hsl_to_rgb(np.array([0.0, 0.0, 0.5]))
        np.testing.assert_allclose(rgb, [0.5, 0.5, 0.5], atol=1e-6)

    def test_hsl_to_rgb_white(self) -> None:
        rgb = hsl_to_rgb(np.array([0.0, 0.0, 1.0]))
        np.testing.assert_allclose(rgb, [1.0, 1.0, 1.0], atol=1e-6)

    def test_rgb_to_hsl_arr_shape(self) -> None:
        image = np.random.default_rng(0).random((3, 3, 3))
        result = rgb_to_hsl_arr(image)
        assert result.shape == (3, 3, 3)

    def test_hsl_to_rgb_arr_shape(self) -> None:
        image = np.random.default_rng(0).random((3, 3, 3))
        hsl = rgb_to_hsl_arr(image)
        rgb = hsl_to_rgb_arr(hsl)
        assert rgb.shape == (3, 3, 3)

    def test_hsl_roundtrip(self) -> None:
        """Converting RGB→HSL→RGB should recover the original values."""
        original = np.array([[[0.2, 0.5, 0.8], [0.9, 0.1, 0.4]]])
        hsl = rgb_to_hsl_arr(original)
        recovered = hsl_to_rgb_arr(hsl)
        np.testing.assert_allclose(recovered, original, atol=1e-6)

    def test_hue_to_rgb_branch_coverage(self) -> None:
        """Test a colour that exercises the t < 2/3 branch in hue_to_rgb."""
        # Cyan: hue=0.5, full saturation
        hsl = np.array([0.5, 1.0, 0.5])
        rgb = hsl_to_rgb(hsl)
        # Cyan should be approximately (0, 1, 1)
        assert rgb[0] < 0.1
        assert rgb[1] > 0.9
        assert rgb[2] > 0.9
