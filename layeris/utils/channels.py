"""Channel manipulation utilities.

The code is based on https://github.com/lukexyz/CV-Instagram-Filters
and has been lightly adapted for this project.
"""

from __future__ import annotations

from typing import Iterable, Tuple

import numpy as np


def split_image_into_channels(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Split an RGB image into its three channels."""

    red_channel = image[:, :, 0]
    green_channel = image[:, :, 1]
    blue_channel = image[:, :, 2]
    return red_channel, green_channel, blue_channel


def merge_channels(red: np.ndarray, green: np.ndarray, blue: np.ndarray) -> np.ndarray:
    """Reconstruct an image from its RGB channels."""

    return np.stack([red, green, blue], axis=2)


def channel_adjust(channel: np.ndarray, values: Iterable[float]) -> np.ndarray:
    """Apply a curve defined by ``values`` to a single colour channel."""

    orig_size = channel.shape
    flat_channel = channel.flatten()
    adjusted = np.interp(flat_channel, np.linspace(0, 1, len(values)), values)
    return adjusted.reshape(orig_size)
