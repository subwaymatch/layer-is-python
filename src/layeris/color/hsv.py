"""
Vectorised conversion between RGB and HSV.

These functions implement the same algorithm as matplotlib.colors.rgb_to_hsv
and matplotlib.colors.hsv_to_rgb (matplotlib was previously a dependency of
this package for these two functions alone) and produce identical results
for float64 inputs in [0, 1].
"""

import numpy as np
from numpy.typing import NDArray


def rgb_to_hsv(rgb: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert an (..., 3) RGB array with values in [0, 1] to HSV."""
    rgb = np.asarray(rgb, dtype=np.float64)
    if rgb.shape[-1] != 3:
        raise ValueError(f"last dimension must be 3 (RGB), got shape {rgb.shape}")

    out = np.zeros_like(rgb)
    value = rgb.max(-1)
    delta = value - rgb.min(-1)

    saturation = np.zeros_like(value)
    positive = value > 0
    saturation[positive] = delta[positive] / value[positive]

    chromatic = delta > 0
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    idx = (red == value) & chromatic
    out[idx, 0] = (green[idx] - blue[idx]) / delta[idx]
    idx = (green == value) & chromatic
    out[idx, 0] = 2.0 + (blue[idx] - red[idx]) / delta[idx]
    idx = (blue == value) & chromatic
    out[idx, 0] = 4.0 + (red[idx] - green[idx]) / delta[idx]

    out[..., 0] = (out[..., 0] / 6.0) % 1.0
    out[..., 1] = saturation
    out[..., 2] = value
    return out


def hsv_to_rgb(hsv: NDArray[np.float64]) -> NDArray[np.float64]:
    """Convert an (..., 3) HSV array with values in [0, 1] to RGB."""
    hsv = np.asarray(hsv, dtype=np.float64)
    if hsv.shape[-1] != 3:
        raise ValueError(f"last dimension must be 3 (HSV), got shape {hsv.shape}")

    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    sector = (h * 6.0).astype(int)
    fraction = (h * 6.0) - sector
    sector %= 6

    p = v * (1.0 - s)
    q = v * (1.0 - s * fraction)
    t = v * (1.0 - s * (1.0 - fraction))

    r = np.choose(sector, [v, q, p, p, t, v])
    g = np.choose(sector, [t, v, v, q, p, p])
    b = np.choose(sector, [p, p, t, v, v, q])

    gray = s == 0
    r = np.where(gray, v, r)
    g = np.where(gray, v, g)
    b = np.where(gray, v, b)

    return np.stack([r, g, b], axis=-1)
