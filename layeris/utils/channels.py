"""
Code from https://github.com/lukexyz/CV-Instagram-Filters (MIT License)

Because the repository didn't have a packaged version, I've copied the relevant functions.
"""

import numpy as np
from numpy.typing import NDArray


def split_image_into_channels(
    image: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    """Split an RGB image array into its three separate channel arrays."""
    red_channel = image[:, :, 0]
    green_channel = image[:, :, 1]
    blue_channel = image[:, :, 2]
    return red_channel, green_channel, blue_channel


def merge_channels(
    red: NDArray[np.float64],
    green: NDArray[np.float64],
    blue: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Merge three channel arrays back into a single RGB image array."""
    return np.stack([red, green, blue], axis=2)


def channel_adjust(
    channel: NDArray[np.float64], values: list[float]
) -> NDArray[np.float64]:
    """Apply a curve adjustment to a single channel using linear interpolation."""
    orig_size = channel.shape
    flat_channel = channel.flatten()
    adjusted = np.interp(flat_channel, np.linspace(0, 1, len(values)), values)
    return adjusted.reshape(orig_size)
