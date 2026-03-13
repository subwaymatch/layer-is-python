import pathlib

import numpy as np
import pytest

from layeris import LayerImage

# Directory that contains the bundled test images.
TEST_IMAGES_DIR = pathlib.Path(__file__).parent / "images"


@pytest.fixture
def white_image() -> LayerImage:
    """4×4 white RGB image (all pixels = 1.0)."""
    return LayerImage.from_array(np.ones((4, 4, 3), dtype=np.float64))


@pytest.fixture
def black_image() -> LayerImage:
    """4×4 black RGB image (all pixels = 0.0)."""
    return LayerImage.from_array(np.zeros((4, 4, 3), dtype=np.float64))


@pytest.fixture
def gray_image() -> LayerImage:
    """4×4 mid-grey RGB image (all pixels = 0.5)."""
    return LayerImage.from_array(np.full((4, 4, 3), 0.5, dtype=np.float64))


@pytest.fixture
def sample_image() -> LayerImage:
    """4×4 RGB image with deterministic random values."""
    rng = np.random.default_rng(42)
    return LayerImage.from_array(rng.random((4, 4, 3)).astype(np.float64))


@pytest.fixture
def rgba_image() -> LayerImage:
    """4×4 RGBA image with a semi-transparent alpha channel."""
    data = np.ones((4, 4, 4), dtype=np.float64) * 0.5
    return LayerImage.from_array(data)


@pytest.fixture
def office_image() -> LayerImage:
    """Real photograph loaded from disk."""
    return LayerImage.from_file(TEST_IMAGES_DIR / "office.jpg")
