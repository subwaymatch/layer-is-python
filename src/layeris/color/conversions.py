import re

import numpy as np
from numpy.typing import NDArray

# Matches '#rgb', 'rgb', '#rrggbb' or 'rrggbb'.
_HEX_COLOR_RE = re.compile(r"\A#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")


def convert_uint_to_float(img_data: NDArray[np.uint8]) -> NDArray[np.float64]:
    return img_data / 255


def convert_float_to_uint(img_data: NDArray[np.float64]) -> NDArray[np.uint8]:
    return round_to_uint(img_data * 255)


def round_to_uint(img_data: NDArray[np.float64]) -> NDArray[np.uint8]:
    return np.round(img_data).astype("uint8")


def _parse_hex(hex_string: str) -> list[int]:
    match = _HEX_COLOR_RE.match(hex_string)
    if match is None:
        raise ValueError(
            f"Invalid hex colour {hex_string!r}: expected '#rgb' or '#rrggbb' "
            "(with or without the leading '#')"
        )
    digits = match.group(1)
    if len(digits) == 3:
        digits = "".join(ch * 2 for ch in digits)
    return [int(digits[i : i + 2], 16) for i in (0, 2, 4)]


def hex_to_rgb(hex_string: str) -> NDArray[np.int_]:
    """Parse a hex colour string into an integer RGB array in [0, 255]."""
    return np.array(_parse_hex(hex_string))


def hex_to_rgb_float(hex_string: str) -> NDArray[np.float64]:
    """Parse a hex colour string into a float RGB array in [0, 1]."""
    return hex_to_rgb(hex_string) / 255


def get_rgb_float_if_hex(blend_data: str | NDArray[np.float64]) -> NDArray[np.float64]:
    if isinstance(blend_data, str):
        return hex_to_rgb_float(blend_data)
    return blend_data


def get_array_from_hex(hex_string: str, height: int, width: int) -> NDArray[np.float64]:
    rgb_as_float = hex_to_rgb_float(hex_string)
    return np.full((height, width, 3), rgb_as_float)
