import numpy as np

from layeris.utils.conversions import (
    convert_float_to_uint,
    convert_uint_to_float,
    get_rgb_float_if_hex,
    hex_to_rgb,
    hex_to_rgb_float,
)


def test_uint_float_roundtrip():
    uint_image = np.array([[0, 128, 255]], dtype=np.uint8)
    float_image = convert_uint_to_float(uint_image)
    assert float_image.dtype == np.float32
    np.testing.assert_allclose(float_image, [[0.0, 128 / 255, 1.0]])

    roundtrip = convert_float_to_uint(float_image)
    assert roundtrip.dtype == np.uint8
    np.testing.assert_array_equal(roundtrip, uint_image)


def test_hex_conversions():
    rgb_uint = hex_to_rgb("#112233")
    np.testing.assert_array_equal(rgb_uint, np.array([17, 34, 51], dtype=np.uint8))

    rgb_float = hex_to_rgb_float("#112233")
    np.testing.assert_allclose(rgb_float, rgb_uint.astype(np.float32) / 255)


def test_get_rgb_float_if_hex_accepts_arrays():
    array = np.array([0.2, 0.4, 0.6])
    result = get_rgb_float_if_hex(array)
    np.testing.assert_allclose(result, array)

    result_from_hex = get_rgb_float_if_hex("#ff0000")
    np.testing.assert_allclose(result_from_hex, np.array([1.0, 0.0, 0.0], dtype=np.float32))
