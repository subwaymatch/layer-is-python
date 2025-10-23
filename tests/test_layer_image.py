import json

import numpy as np
import pytest

from layeris import LayerImage


@pytest.fixture
def sample_image():
    return np.zeros((2, 2, 3), dtype=np.uint8)


def test_clone_produces_independent_copy(sample_image):
    image = LayerImage.from_array(sample_image)
    clone = image.clone()

    clone.lightness(0.5)
    original = image.get_image_as_array()
    modified = clone.get_image_as_array()

    np.testing.assert_array_equal(original, np.zeros_like(original))
    assert not np.allclose(original, modified)


def test_apply_from_json(tmp_path, sample_image):
    image = LayerImage.from_array(sample_image)
    json_data = {
        "operations": [
            {"type": "brightness", "factor": 0.2},
            {"type": "saturation", "factor": 0.0},
        ]
    }
    json_path = tmp_path / "ops.json"
    json_path.write_text(json.dumps(json_data), encoding="utf-8")

    image.apply_from_json(json_path)
    result = image.get_image_as_array()

    np.testing.assert_allclose(result, np.full_like(result, 0.2))
