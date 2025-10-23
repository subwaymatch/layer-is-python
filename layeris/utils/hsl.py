"""RGB and HSL conversion helpers."""

from __future__ import annotations

from typing import Sequence

import numpy as np


def rgb_to_hsl_arr(image_data: np.ndarray) -> np.ndarray:
    """Convert an RGB image array to HSL using :func:`rgb_to_hsl`."""

    return np.apply_along_axis(rgb_to_hsl, -1, image_data)


def hsl_to_rgb_arr(image_data: np.ndarray) -> np.ndarray:
    """Convert an HSL image array to RGB using :func:`hsl_to_rgb`."""

    return np.apply_along_axis(hsl_to_rgb, -1, image_data)


def rgb_to_hsl(rgb_as_float: Sequence[float]) -> np.ndarray:
    """Convert a single RGB colour (``0.0`` – ``1.0``) to HSL."""

    r, g, b = rgb_as_float
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, l = ((high + low) / 2,) * 3

    if high == low:
        h = 0.0
        s = 0.0
    else:
        d = high - low
        l = (high + low) / 2
        s = d / (2 - high - low) if l > 0.5 else d / (high + low)
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return np.array([h, s, l], dtype=np.float32)


def hsl_to_rgb(hsl_as_float: Sequence[float]) -> np.ndarray:
    """Convert a single HSL colour to RGB (``0.0`` – ``1.0``)."""

    h, s, l = hsl_as_float

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        t += 1 if t < 0 else 0
        t -= 1 if t > 1 else 0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)

    return np.array([r, g, b], dtype=np.float32)
