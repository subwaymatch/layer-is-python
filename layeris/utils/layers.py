"""Blend mode helpers."""

from __future__ import annotations

import numpy as np


def mix(base_image_data: np.ndarray, blend_data: np.ndarray, blend_opacity: float) -> np.ndarray:
    """Return a linear blend between ``base_image_data`` and ``blend_data``."""

    blend_opacity = float(np.clip(blend_opacity, 0.0, 1.0))
    if blend_opacity < 1.0:
        return base_image_data * (1.0 - blend_opacity) + blend_data * blend_opacity

    return blend_data
