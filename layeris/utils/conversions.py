"""Conversion helpers for image manipulation."""

from __future__ import annotations

from typing import Iterable, Union

import numpy as np


ArrayLike = Union[np.ndarray, Iterable[float]]


def convert_uint_to_float(img_data: np.ndarray) -> np.ndarray:
    """Normalise an unsigned integer RGB array to the ``0.0`` – ``1.0`` range."""

    return img_data.astype(np.float32) / 255


def convert_float_to_uint(img_data: np.ndarray) -> np.ndarray:
    """Convert a normalised float RGB array back to ``uint8``."""

    return round_to_uint(np.clip(img_data, 0.0, 1.0) * 255)


def round_to_uint(img_data: np.ndarray) -> np.ndarray:
    """Round a floating point array and cast it to ``uint8``."""

    return np.round(img_data).astype("uint8")


def hex_to_rgb(hex_string: str) -> np.ndarray:
    """Convert a hexadecimal colour string (``#RRGGBB``) to ``uint8`` RGB values."""

    return np.array(
        [int(hex_string.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)],
        dtype="uint8",
    )


def hex_to_rgb_float(hex_string: str) -> np.ndarray:
    """Convert a hexadecimal colour string to normalised float RGB values."""

    return convert_uint_to_float(hex_to_rgb(hex_string))


def get_rgb_float_if_hex(blend_data: Union[str, ArrayLike]) -> np.ndarray:
    """Ensure blend data is represented as a float RGB array."""

    if isinstance(blend_data, str):
        return hex_to_rgb_float(blend_data)

    array = np.asarray(blend_data, dtype=np.float32)
    return np.clip(array, 0.0, 1.0)


def get_array_from_hex(hex_string: str, height: int, width: int) -> np.ndarray:
    """Create a float RGB array of the given size filled with ``hex_string`` colour."""

    rgb_as_float = hex_to_rgb_float(hex_string)
    return np.full((height, width, 3), rgb_as_float, dtype=np.float32)
