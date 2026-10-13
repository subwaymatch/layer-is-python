from __future__ import annotations

import json
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import requests
from numpy.typing import NDArray
from PIL import Image, ImageOps

from .channels import channel_adjust, merge_channels, split_image_into_channels
from .color.conversions import (
    convert_float_to_uint,
    convert_uint_to_float,
    get_rgb_float_if_hex,
)
from .color.hsv import hsv_to_rgb, rgb_to_hsv
from .blend import mix

# Blend mode operation names that accept a hex colour and opacity parameter.
_BLEND_MODES: frozenset[str] = frozenset(
    {
        "darken",
        "multiply",
        "color_burn",
        "linear_burn",
        "lighten",
        "screen",
        "color_dodge",
        "linear_dodge",
        "overlay",
        "soft_light",
        "hard_light",
        "vivid_light",
        "linear_light",
        "pin_light",
    }
)


_Array = NDArray[np.float64]
# An operation applied to RGB data of shape (H, W, 3).
_RGBFunc = Callable[[_Array], _Array]
# A blend-mode formula: (base A, blend layer B) -> blended result.
_BlendFunc = Callable[[_Array, _Array], _Array]


def _identity_lut() -> NDArray[np.float64]:
    """A 1x256 RGB "image" holding every 8-bit level once, as floats in [0, 1].

    Running a per-channel operation on it yields that operation's lookup
    table: entry ``[0, v, c]`` is the result for input level ``v`` in
    channel ``c``. The levels are computed exactly as ``from_file`` would
    convert 8-bit pixels (``v / 255``), so the table holds bit-identical
    values to processing the full image in float64.
    """
    levels = np.arange(256) / 255
    return np.repeat(levels[np.newaxis, :, np.newaxis], 3, axis=2)


def _is_uniform(blend_data: NDArray[np.float64]) -> bool:
    """True when a blend layer has the same value at every pixel.

    That is the case for hex colours and for arrays that only vary by
    channel, such as shape (3,) or (1, 1, 3).
    """
    shape = np.shape(blend_data)
    return len(shape) <= 3 and all(n == 1 for n in shape[:-1])


class LayerImage:
    """An RGB or RGBA image with Photoshop-style adjustments and blend modes.

    Every operation mutates the image in place and returns it, so calls can
    be chained.

    Photos loaded with :meth:`from_file` or :meth:`from_url` are kept as
    8-bit Pillow images for as long as possible. Operations that change each
    channel based only on that channel's own value (brightness, contrast,
    lightness, curves and blend modes with a uniform colour) are folded into
    a single 256-entry lookup table instead of being run on every pixel, and
    Pillow applies the table in one pass when the image is resized or saved.
    Operations that need float pixels (:meth:`get_image_as_array`,
    grayscale, hue, saturation and blending with a per-pixel array) convert
    the image to float64 once and continue from there. Results are identical
    to processing every pixel in float64.
    """

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def from_url(url: str, timeout: float = 30.0) -> LayerImage:
        """Download an image over HTTP(S) and wrap it in a LayerImage.

        Raises requests.HTTPError for non-2xx responses instead of failing
        later with a cryptic image-decoding error.
        """
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return LayerImage._from_pil(LayerImage._normalize_pil_image(image))

    @staticmethod
    def from_file(file_path: str | Path) -> LayerImage:
        image = Image.open(file_path)
        return LayerImage._from_pil(LayerImage._normalize_pil_image(image))

    @staticmethod
    def from_array(image_data: NDArray[np.float64]) -> LayerImage:
        """Wrap a float array of shape (H, W, 3|4) with values in [0, 1]."""
        return LayerImage(image_data)

    # ------------------------------------------------------------------
    # PIL normalisation helper
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_pil_image(image: Image.Image) -> Image.Image:
        """Convert any PIL image mode to RGB or RGBA for consistent processing."""
        # Apply EXIF orientation so photos from cameras/phones load upright.
        image = ImageOps.exif_transpose(image)
        if image.mode == "RGBA":
            return image
        if image.mode == "RGB":
            return image
        if image.mode == "P":
            return image.convert("RGBA" if "transparency" in image.info else "RGB")
        if image.mode in ("L", "CMYK", "YCbCr", "LAB", "HSV"):
            return image.convert("RGB")
        if image.mode == "LA":
            return image.convert("RGBA")
        return image.convert("RGB")

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self, image_data: NDArray[np.float64]) -> None:
        # image_data is always a float array in [0, 1],
        # shape (H, W, 3) for RGB or (H, W, 4) for RGBA
        image_data = np.asarray(image_data)
        if not np.issubdtype(image_data.dtype, np.floating):
            raise TypeError(
                f"image_data must be a float array with values in [0, 1], "
                f"got dtype {image_data.dtype}. Use LayerImage.from_file() / "
                "from_url() to load 8-bit images, or divide the array by 255."
            )
        if image_data.ndim != 3 or image_data.shape[2] not in (3, 4):
            raise ValueError(
                "image_data must have shape (height, width, 3) for RGB or "
                f"(height, width, 4) for RGBA, got {image_data.shape}"
            )
        # Pixels live in exactly one of two forms:
        # - float mode: _data holds the float64 pixels;
        # - 8-bit mode: _pil holds the photo as loaded and _lut the pending
        #   per-channel operations (None when there are none).
        self._data: NDArray[np.float64] | None = image_data.astype(np.float64)
        self._pil: Image.Image | None = None
        self._lut: NDArray[np.float64] | None = None

    @staticmethod
    def _from_pil(image: Image.Image) -> LayerImage:
        """Wrap an 8-bit RGB or RGBA Pillow image without converting it to floats."""
        image.load()
        # Drop metadata (EXIF, DPI, ICC profile, PNG transparency key) so that
        # saved files contain only the pixels, as they always have.
        image.info = {}
        layer = LayerImage.__new__(LayerImage)
        layer._data = None
        layer._pil = image
        layer._lut = None
        return layer

    # ------------------------------------------------------------------
    # Pixel storage (internal)
    # ------------------------------------------------------------------

    @property
    def image_data(self) -> NDArray[np.float64]:
        """The pixels as a float64 array in [0, 1], shape (H, W, 3) or (H, W, 4).

        Reading it switches an 8-bit photo to float mode for good.
        """
        self._use_float_pixels()
        assert self._data is not None
        return self._data

    @image_data.setter
    def image_data(self, value: NDArray[np.float64]) -> None:
        self._data = value
        self._pil = None
        self._lut = None

    def _use_float_pixels(self) -> None:
        """Switch an 8-bit photo to float64 pixels (no-op if already float)."""
        if self._data is None:
            self._data = self._float_pixels()
            self._pil = None
            self._lut = None

    def _float_pixels(self) -> NDArray[np.float64]:
        """Current pixels as float64 without changing how they are stored."""
        if self._data is not None:
            return self._data
        assert self._pil is not None
        pixels = np.asarray(self._pil)
        if self._lut is None:
            return convert_uint_to_float(pixels)
        rgb = np.stack(
            [self._lut[0, :, c][pixels[:, :, c]] for c in range(3)], axis=-1
        )
        if pixels.shape[2] == 4:
            alpha = convert_uint_to_float(pixels[:, :, 3:4])
            return np.concatenate([rgb, alpha], axis=2)
        return rgb

    def _point_table(self) -> list[int]:
        """The pending lookup table in the form Pillow's ``Image.point`` takes."""
        assert self._pil is not None and self._lut is not None
        # Round exactly like the float path does when it converts to 8-bit.
        table = convert_float_to_uint(self._lut[0])
        bands = [table[:, c] for c in range(3)]
        if self._pil.mode == "RGBA":
            bands.append(np.arange(256, dtype=np.uint8))
        return [int(v) for v in np.concatenate(bands)]

    def _apply_per_channel(self, func: _RGBFunc) -> LayerImage:
        """Apply *func*, where each output channel depends only on the same input
        channel, so it can be folded into an 8-bit photo's lookup table."""
        if self._pil is not None:
            # 8-bit photo: fold the operation into the lookup table.
            self._lut = func(self._lut if self._lut is not None else _identity_lut())
        else:
            self.image_data = self._reattach_alpha(func(self._rgb()))
        return self

    def _blend(
        self,
        blend_data: str | NDArray[np.float64],
        opacity: float,
        formula: _BlendFunc,
    ) -> LayerImage:
        B = get_rgb_float_if_hex(blend_data)
        if not _is_uniform(B):
            # A per-pixel layer (gradient, texture, another photo) cannot be
            # expressed as a lookup table, so switch to float pixels first.
            self._use_float_pixels()
        return self._apply_per_channel(lambda A: mix(A, formula(A, B), opacity))

    # ------------------------------------------------------------------
    # Alpha helpers (internal)
    # ------------------------------------------------------------------

    def _has_alpha(self) -> bool:
        if self._pil is not None:
            return self._pil.mode == "RGBA"
        assert self._data is not None
        return self._data.ndim == 3 and self._data.shape[2] == 4

    def _get_alpha(self) -> NDArray[np.float64] | None:
        """Return the alpha channel as (H, W, 1) or None."""
        if self._has_alpha():
            return self.image_data[:, :, 3:4]
        return None

    def _rgb(self) -> NDArray[np.float64]:
        """Return a view of the RGB channels only."""
        return self.image_data[:, :, :3]

    def _reattach_alpha(self, rgb_data: NDArray[np.float64]) -> NDArray[np.float64]:
        """Combine processed RGB data with the original alpha channel (if any)."""
        alpha = self._get_alpha()
        if alpha is not None:
            return np.concatenate([rgb_data, alpha], axis=2)
        return rgb_data

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resize(self, width: int, height: int) -> LayerImage:
        """Resize the image to (width, height) using high-quality Lanczos resampling."""
        if width < 1 or height < 1:
            raise ValueError(f"width and height must be >= 1, got ({width}, {height})")
        if self._pil is not None:
            # Resizing works on 8-bit pixels anyway, so an 8-bit photo stays one.
            self._pil = self._to_pil_image().resize(
                (width, height), Image.Resampling.LANCZOS
            )
            self._lut = None
            return self
        uint_data = convert_float_to_uint(self.image_data)
        mode = "RGBA" if self._has_alpha() else "RGB"
        pil_image = Image.fromarray(uint_data, mode=mode)
        pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)
        self.image_data = convert_uint_to_float(np.asarray(pil_image)).astype(
            np.float64
        )
        return self

    # ------------------------------------------------------------------
    # Adjustments
    # ------------------------------------------------------------------

    def grayscale(self) -> LayerImage:
        gray = np.dot(self._rgb(), [0.2989, 0.5870, 0.1140])
        rgb_result = np.stack((gray,) * 3, axis=-1)
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def brightness(self, factor: float) -> LayerImage:
        return self._apply_per_channel(lambda rgb: np.clip(rgb * (1 + factor), 0, 1))

    def contrast(self, factor: float) -> LayerImage:
        return self._apply_per_channel(
            lambda rgb: np.clip(factor * (rgb - 0.5) + 0.5, 0, 1)
        )

    def hue(self, target_hue: float) -> LayerImage:
        """Set every pixel's hue to *target_hue* (in [0, 1]), keeping
        saturation and value (a colorize-style adjustment)."""
        hsv = rgb_to_hsv(self._rgb())
        hsv[:, :, 0] = target_hue
        self.image_data = self._reattach_alpha(hsv_to_rgb(hsv))
        return self

    def saturation(self, factor: float) -> LayerImage:
        hsv = rgb_to_hsv(self._rgb())
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + factor), 0, 1)
        self.image_data = self._reattach_alpha(hsv_to_rgb(hsv))
        return self

    def lightness(self, factor: float) -> LayerImage:
        def adjust(rgb: _Array) -> _Array:
            if factor > 0:
                return rgb + (1 - rgb) * factor
            if factor < 0:
                return rgb + rgb * factor
            return rgb.copy()

        return self._apply_per_channel(adjust)

    def curve(
        self, channels: str = "rgb", curve_points: list[float] | None = None
    ) -> LayerImage:
        if not channels or set(channels) - set("rgb"):
            raise ValueError(
                f"channels must be a non-empty combination of 'r', 'g' and 'b' "
                f"(e.g. 'rgb' or 'rg'), got {channels!r}"
            )
        points = [0.0, 1.0] if curve_points is None else curve_points

        def adjust(rgb: _Array) -> _Array:
            r, g, b = split_image_into_channels(rgb)
            if "r" in channels:
                r = channel_adjust(r, points)
            if "g" in channels:
                g = channel_adjust(g, points)
            if "b" in channels:
                b = channel_adjust(b, points)
            return merge_channels(r, g, b)

        return self._apply_per_channel(adjust)

    # ------------------------------------------------------------------
    # Blend modes (darken group)
    # ------------------------------------------------------------------

    def darken(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(blend_data, opacity, np.minimum)

    def multiply(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(blend_data, opacity, lambda A, B: A * B)

    def color_burn(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        def formula(A: _Array, B: _Array) -> _Array:
            with np.errstate(divide="ignore", invalid="ignore"):
                return np.clip(np.where(B > 0, 1 - (1 - A) / B, 0), 0, 1)

        return self._blend(blend_data, opacity, formula)

    def linear_burn(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(blend_data, opacity, lambda A, B: np.clip(A + B - 1, 0, 1))

    # ------------------------------------------------------------------
    # Blend modes (lighten group)
    # ------------------------------------------------------------------

    def lighten(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(blend_data, opacity, np.maximum)

    def screen(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(blend_data, opacity, lambda A, B: 1 - (1 - A) * (1 - B))

    def color_dodge(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        def formula(A: _Array, B: _Array) -> _Array:
            with np.errstate(divide="ignore", invalid="ignore"):
                return np.where(B == 1, B, np.clip(A / (1 - B), 0, 1))

        return self._blend(blend_data, opacity, formula)

    def linear_dodge(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(blend_data, opacity, lambda A, B: np.clip(A + B, 0, 1))

    # ------------------------------------------------------------------
    # Blend modes (contrast group)
    # ------------------------------------------------------------------

    def overlay(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(
            blend_data,
            opacity,
            lambda A, B: np.where(A <= 0.5, 2 * A * B, 1 - 2 * (1 - A) * (1 - B)),
        )

    def soft_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        def formula(A: _Array, B: _Array) -> _Array:
            data01 = 2 * A * B + np.square(A) * (1 - 2 * B)
            data02 = np.sqrt(A) * (2 * B - 1) + 2 * A * (1 - B)
            return np.where(B <= 0.5, data01, data02)

        return self._blend(blend_data, opacity, formula)

    def hard_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(
            blend_data,
            opacity,
            lambda A, B: np.where(B <= 0.5, 2 * A * B, 1 - 2 * (1 - A) * (1 - B)),
        )

    def vivid_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        def formula(A: _Array, B: _Array) -> _Array:
            with np.errstate(divide="ignore", invalid="ignore"):
                color_burn = np.where(B > 0, 1 - (1 - A) / (2 * B), 0)
                color_dodge = np.where(B < 1, A / (2 * (1 - B)), 1)
            return np.clip(np.where(B <= 0.5, color_burn, color_dodge), 0, 1)

        return self._blend(blend_data, opacity, formula)

    def linear_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(
            blend_data, opacity, lambda A, B: np.clip(A + 2 * B - 1, 0, 1)
        )

    def pin_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        return self._blend(
            blend_data,
            opacity,
            lambda A, B: np.clip(
                np.where(A < 2 * B - 1, 2 * B - 1, np.where(A > 2 * B, 2 * B, A)),
                0,
                1,
            ),
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clone(self) -> LayerImage:
        if self._pil is not None:
            twin = LayerImage._from_pil(self._pil.copy())
            twin._lut = None if self._lut is None else self._lut.copy()
            return twin
        return LayerImage.from_array(self.image_data.copy())

    def get_image_as_array(self) -> NDArray[np.float64]:
        """Return the underlying float64 array (not a copy).

        For a photo loaded from a file or URL, this applies any pending
        per-channel operations and keeps the image in float64 from then on.
        """
        return self.image_data

    def __repr__(self) -> str:
        if self._pil is not None:
            width, height = self._pil.size
        else:
            height, width = self.image_data.shape[:2]
        mode = "RGBA" if self._has_alpha() else "RGB"
        return f"<LayerImage {mode} {width}x{height}>"

    def _to_pil_image(self) -> Image.Image:
        """Build an 8-bit PIL image of the current pixels (resize, save, display)."""
        if self._pil is not None:
            if self._lut is None:
                return self._pil
            return self._pil.point(self._point_table())
        uint_data = convert_float_to_uint(self.image_data)
        mode = "RGBA" if self._has_alpha() else "RGB"
        return Image.fromarray(uint_data, mode=mode)

    def _repr_png_(self) -> bytes:
        """Return PNG bytes so Jupyter displays the actual image preview."""
        buffer = BytesIO()
        self._to_pil_image().save(buffer, format="PNG")
        return buffer.getvalue()

    # ------------------------------------------------------------------
    # JSON / dict operation sequencing
    # ------------------------------------------------------------------

    def apply_from_dict(self, data: dict[str, Any]) -> LayerImage:
        """Apply a sequence of operations defined in a Python dictionary.

        Expected format::

            {
                "operations": [
                    {"type": "grayscale"},
                    {"type": "brightness", "factor": 0.2},
                    {"type": "multiply", "hex": "#ff0000", "opacity": 0.5},
                    {"type": "resize", "width": 800, "height": 600},
                    {"type": "curve", "channels": "rgb", "curve_points": [0, 0.5, 1]},
                    ...
                ]
            }
        """
        for op in data.get("operations", []):
            op_type = op.get("type")
            hex_string = op.get("hex")
            opacity = op.get("opacity", 1.0)
            factor = op.get("factor")

            if op_type == "grayscale":
                self.grayscale()
            elif op_type == "resize":
                if "width" in op and "height" in op:
                    self.resize(op["width"], op["height"])
            elif op_type == "brightness":
                if factor is not None:
                    self.brightness(factor)
            elif op_type == "contrast":
                if factor is not None:
                    self.contrast(factor)
            elif op_type == "hue":
                if "hue" in op:
                    self.hue(op["hue"])
            elif op_type == "saturation":
                if factor is not None:
                    self.saturation(factor)
            elif op_type == "lightness":
                if factor is not None:
                    self.lightness(factor)
            elif op_type == "curve":
                if "channels" in op and "curve_points" in op:
                    self.curve(op["channels"], op["curve_points"])
            elif op_type in _BLEND_MODES and hex_string is not None:
                getattr(self, op_type)(hex_string, opacity)

        return self

    def apply_from_json(self, filepath: str | Path) -> LayerImage:
        """Load a JSON file and apply the operation sequence it defines."""
        with open(filepath) as f:
            data = json.load(f)
        return self.apply_from_dict(data)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, filename: str | Path, quality: int = 95) -> LayerImage:
        """Save the image to *filename*.

        Supported formats are determined by the file extension (JPEG, PNG,
        BMP, TIFF, WebP, etc.).  When saving an RGBA image as JPEG the alpha
        channel is composited onto a white background automatically.
        """
        filename_str = str(filename)
        is_jpeg = filename_str.lower().endswith((".jpg", ".jpeg"))

        if is_jpeg and self._has_alpha():
            # Composite alpha onto white before saving as JPEG
            pixels = self._float_pixels()
            rgb = pixels[:, :, :3]
            alpha = pixels[:, :, 3:4]
            composited = rgb * alpha + (1 - alpha)
            uint_data = convert_float_to_uint(composited)
            Image.fromarray(uint_data, mode="RGB").save(filename, quality=quality)
        elif is_jpeg:
            self._to_pil_image().convert("RGB").save(filename, quality=quality)
        else:
            self._to_pil_image().save(filename)

        return self
