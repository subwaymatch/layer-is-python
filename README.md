<p align="center">
<img src="https://user-images.githubusercontent.com/1064036/66263389-f9e12e00-e82c-11e9-87d4-1b792fb16c7b.png">
</p>

# Layer.is

A library that supports all blend modes in Photoshop, brightness, contrast, hue, saturation, lightness adjustments, and curve adjustments on separate RGB channels.

This project was a part of the 2019 Open Source Software Competition.

- [Introductory video](https://www.youtube.com/watch?v=PU_tEd8JgCw)
- [OSS Project Link](https://www.oss.kr/dev_competition_activities/show/b6c44d4b-e557-4ff1-adcc-5625216fddc8?page=3)

## Why use Layer.is?

- Supports all frequently used blend modes in Photoshop
- Chain operations for concise, readable image pipelines
- Straightforward API to manipulate images
- Load a sequence of operations from JSON
- Apply curve adjustments selectively to individual RGB channels

## Requirements

Python 3.10 or higher.

## Installation

### From PyPI

```sh
pip install layeris
```

### From source

```sh
git clone https://github.com/subwaymatch/layer-is-python.git
cd layer-is-python
pip install -e .
```

To install with development dependencies (includes pytest):

```sh
pip install -e ".[dev]"
# or, using hatch:
hatch env create
```

> **Contributor note:** The package uses a `src/` layout — the importable package lives under `src/layeris/`. Run `pip install -e .` from the repo root for an editable install that picks up changes automatically. Tests live in `tests/` and are discovered by pytest automatically.

## Quick Start

### Load an image

```python
from layeris import LayerImage

# From a local file
image = LayerImage.from_file('/path/to/image.jpg')

# From a URL
image = LayerImage.from_url('https://example.com/photo.jpg')

# From a NumPy array (float64, values in [0, 1], shape HxWx3 or HxWx4)
import numpy as np
data = np.random.random((100, 100, 3))
image = LayerImage.from_array(data)
```

### Save an image

```python
# Default quality is 95 for JPEG
image.save('output.jpg')

# Specify JPEG quality (0–100)
image.save('output.jpg', quality=85)

# Save as PNG (lossless)
image.save('output.png')
```

### Basic adjustments

```python
# Grayscale
image.grayscale()

# Brightness  (factor > 0 brightens, factor < 0 darkens)
image.brightness(0.2)

# Contrast  (factor > 1 increases, 0 < factor < 1 decreases)
image.contrast(1.5)

# Hue  (value in [0, 1])
image.hue(0.3)

# Saturation  (factor > 0 increases, factor < 0 decreases; -1 fully desaturates)
image.saturation(-0.5)

# Lightness  (factor > 0 lightens toward white, factor < 0 darkens toward black)
image.lightness(0.4)

# Curve adjustment (apply an S-curve to the RGB channels)
image.curve('rgb', [0, 0.1, 0.4, 0.65, 0.9, 1])

# Curve on a single channel
image.curve('r', [0, 0.2, 0.8, 1])
```

### Resize

```python
image.resize(width=800, height=600)
```

### Blend modes

All blend mode methods accept a hex colour string **or** a NumPy array, plus an optional `opacity` parameter (0.0–1.0).

#### Darken group

```python
image.darken('#3fe28f')
image.multiply('#3fe28f', opacity=0.8)
image.color_burn('#7fe3f8')
image.linear_burn('#e1a8ff')
```

#### Lighten group

```python
image.lighten('#ff3ce1')
image.screen('#e633ba')
image.color_dodge('#490cc7')
image.linear_dodge('#490cc7')
```

#### Contrast group

```python
image.overlay('#ffb956')
image.soft_light('#ff3cbc')
image.hard_light('#df5dff')
image.vivid_light('#ac5b7f')
image.linear_light('#9fa500')
image.pin_light('#005546')
```

### Method chaining

All operations return `self`, so calls can be chained:

```python
result = (
    LayerImage.from_file('photo.jpg')
    .grayscale()
    .brightness(0.1)
    .multiply('#3fe28f', opacity=0.7)
    .curve('rgb', [0, 0.2, 0.8, 1])
    .save('output.jpg')
)
```

### Clone

```python
# Create an independent copy before branching
copy = image.clone()
copy.darken('#000000')  # original is unaffected
```

### Get image data as a NumPy array

```python
arr = image.get_image_as_array()
# arr.shape  → (height, width, 3)  for RGB
#            → (height, width, 4)  for RGBA
# arr.dtype  → float64
# values in [0.0, 1.0]
```

### Apply operations from a dictionary or JSON file

Operations can be described as a Python dict (or a JSON file) and applied in sequence:

```python
ops = {
    "operations": [
        {"type": "grayscale"},
        {"type": "brightness", "factor": 0.15},
        {"type": "multiply", "hex": "#3fe28f", "opacity": 0.6},
        {"type": "curve", "channels": "rgb", "curve_points": [0, 0.1, 0.9, 1]},
        {"type": "resize", "width": 800, "height": 600},
    ]
}

image.apply_from_dict(ops)

# Or load directly from a JSON file
image.apply_from_json('pipeline.json')
```

Supported operation types: `grayscale`, `resize`, `brightness`, `contrast`, `hue`,
`saturation`, `lightness`, `curve`, `darken`, `multiply`, `color_burn`,
`linear_burn`, `lighten`, `screen`, `color_dodge`, `linear_dodge`, `overlay`,
`soft_light`, `hard_light`, `vivid_light`, `linear_light`, `pin_light`.

---

## Running tests

Install development dependencies and run the test suite with pytest:

```sh
# Using pip (editable install)
pip install -e .
pip install pytest pytest-cov
pytest

# Using hatch (recommended)
hatch run test

# With coverage report
hatch run test-cov
```

Run a specific test file or test:

```sh
pytest tests/test_layer_image.py
pytest tests/test_utils.py
pytest tests/test_layer_image.py::TestBlendModes::test_multiply_by_white_no_change -v
```

Test images used by the suite are stored in `tests/images/`.

---

## Blend mode reference

| Group    | Method          | Formula (A = base, B = blend)                         |
|----------|-----------------|-------------------------------------------------------|
| Darken   | `darken`        | `min(A, B)`                                           |
| Darken   | `multiply`      | `A × B`                                               |
| Darken   | `color_burn`    | `1 − (1 − A) / B`                                    |
| Darken   | `linear_burn`   | `A + B − 1`                                           |
| Lighten  | `lighten`       | `max(A, B)`                                           |
| Lighten  | `screen`        | `1 − (1 − A)(1 − B)`                                 |
| Lighten  | `color_dodge`   | `A / (1 − B)`                                        |
| Lighten  | `linear_dodge`  | `A + B`                                               |
| Contrast | `overlay`       | `2AB` if A ≤ 0.5 else `1 − 2(1−A)(1−B)`             |
| Contrast | `soft_light`    | Pegtop formula                                        |
| Contrast | `hard_light`    | `2AB` if B ≤ 0.5 else `1 − 2(1−A)(1−B)`             |
| Contrast | `vivid_light`   | Color burn / dodge based on B                         |
| Contrast | `linear_light`  | `A + 2B − 1`                                          |
| Contrast | `pin_light`     | Conditional replace                                   |

All results are clamped to `[0, 1]`.

---

## Roadmap

- Imitate Photoshop's auto brightness & auto contrast features
- Add filter presets
