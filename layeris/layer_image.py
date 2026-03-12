from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Any

import matplotlib.colors
import numpy as np
import requests
from numpy.typing import NDArray
from PIL import Image

from .utils.channels import channel_adjust, merge_channels, split_image_into_channels
from .utils.conversions import (
    convert_float_to_uint,
    convert_uint_to_float,
    get_rgb_float_if_hex,
)
from .utils.layers import mix

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


class LayerImage:
    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def from_url(url: str) -> LayerImage:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image = LayerImage._normalize_pil_image(image)
        return LayerImage(convert_uint_to_float(np.asarray(image)))

    @staticmethod
    def from_file(file_path: str | Path) -> LayerImage:
        image = Image.open(file_path)
        image = LayerImage._normalize_pil_image(image)
        return LayerImage(convert_uint_to_float(np.asarray(image)))

    @staticmethod
    def from_array(image_data: NDArray[np.float64]) -> LayerImage:
        return LayerImage(image_data)

    # ------------------------------------------------------------------
    # PIL normalisation helper
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_pil_image(image: Image.Image) -> Image.Image:
        """Convert any PIL image mode to RGB or RGBA for consistent processing."""
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
        # image_data is always a float32/float64 array in [0, 1]
        # shape is (H, W, 3) for RGB or (H, W, 4) for RGBA
        self.image_data: NDArray[np.float64] = image_data.astype(np.float64)

    # ------------------------------------------------------------------
    # Alpha helpers (internal)
    # ------------------------------------------------------------------

    def _has_alpha(self) -> bool:
        return self.image_data.ndim == 3 and self.image_data.shape[2] == 4

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
        uint_data = convert_float_to_uint(self.image_data)
        mode = "RGBA" if self._has_alpha() else "RGB"
        pil_image = Image.fromarray(uint_data, mode=mode)
        pil_image = pil_image.resize((width, height), Image.LANCZOS)
        self.image_data = convert_uint_to_float(np.asarray(pil_image)).astype(np.float64)
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
        rgb_result = np.clip(self._rgb() * (1 + factor), 0, 1)
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def contrast(self, factor: float) -> LayerImage:
        rgb_result = np.clip(factor * (self._rgb() - 0.5) + 0.5, 0, 1)
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def hue(self, target_hue: float) -> LayerImage:
        hsv = matplotlib.colors.rgb_to_hsv(self._rgb())
        hsv[:, :, 0] = target_hue
        self.image_data = self._reattach_alpha(matplotlib.colors.hsv_to_rgb(hsv))
        return self

    def saturation(self, factor: float) -> LayerImage:
        hsv = matplotlib.colors.rgb_to_hsv(self._rgb())
        hsv = np.clip(hsv + hsv * [0, factor, 0], 0, 1)
        self.image_data = self._reattach_alpha(matplotlib.colors.hsv_to_rgb(hsv))
        return self

    def lightness(self, factor: float) -> LayerImage:
        rgb = self._rgb()
        if factor > 0:
            rgb_result = rgb + (1 - rgb) * factor
        elif factor < 0:
            rgb_result = rgb + rgb * factor
        else:
            rgb_result = rgb.copy()
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def curve(
        self, channels: str = "rgb", curve_points: list[float] | None = None
    ) -> LayerImage:
        if curve_points is None:
            curve_points = [0, 1]
        r, g, b = split_image_into_channels(self._rgb())
        if "r" in channels:
            r = channel_adjust(r, curve_points)
        if "g" in channels:
            g = channel_adjust(g, curve_points)
        if "b" in channels:
            b = channel_adjust(b, curve_points)
        self.image_data = self._reattach_alpha(merge_channels(r, g, b))
        return self

    # ------------------------------------------------------------------
    # Blend modes (darken group)
    # ------------------------------------------------------------------

    def darken(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.minimum(A, blend_data)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def multiply(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = A * blend_data
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def color_burn(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.clip(np.where(B > 0, 1 - (1 - A) / B, 0), 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def linear_burn(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.clip(A + blend_data - 1, 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    # ------------------------------------------------------------------
    # Blend modes (lighten group)
    # ------------------------------------------------------------------

    def lighten(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.maximum(A, blend_data)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def screen(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = 1 - (1 - A) * (1 - B)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def color_dodge(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.where(B == 1, B, np.clip(A / (1 - B), 0, 1))
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def linear_dodge(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.clip(A + blend_data, 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    # ------------------------------------------------------------------
    # Blend modes (contrast group)
    # ------------------------------------------------------------------

    def overlay(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = np.where(A <= 0.5, 2 * A * B, 1 - 2 * (1 - A) * (1 - B))
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def soft_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        data01 = 2 * A * B + np.square(A) * (1 - 2 * B)
        data02 = np.sqrt(A) * (2 * B - 1) + 2 * A * (1 - B)
        result = np.where(B <= 0.5, data01, data02)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def hard_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = np.where(B <= 0.5, 2 * A * B, 1 - 2 * (1 - A) * (1 - B))
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def vivid_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        with np.errstate(divide="ignore", invalid="ignore"):
            color_burn = np.where(B > 0, 1 - (1 - A) / (2 * B), 0)
            color_dodge = np.where(B < 1, A / (2 * (1 - B)), 1)
        result = np.clip(np.where(B <= 0.5, color_burn, color_dodge), 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def linear_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.clip(A + 2 * blend_data - 1, 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def pin_light(
        self, blend_data: str | NDArray[np.float64], opacity: float = 1.0
    ) -> LayerImage:
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = np.clip(
            np.where(A < 2 * B - 1, 2 * B - 1, np.where(A > 2 * B, 2 * B, A)),
            0,
            1,
        )
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def clone(self) -> LayerImage:
        return LayerImage.from_array(self.image_data.copy())

    def get_image_as_array(self) -> NDArray[np.float64]:
        return self.image_data

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
        BMP, TIFF, WebP, …).  When saving an RGBA image as JPEG the alpha
        channel is composited onto a white background automatically.
        """
        filename_str = str(filename)
        is_jpeg = filename_str.lower().endswith((".jpg", ".jpeg"))

        if is_jpeg and self._has_alpha():
            # Composite alpha onto white before saving as JPEG
            rgb = self._rgb()
            alpha = self.image_data[:, :, 3:4]
            composited = rgb * alpha + (1 - alpha)
            uint_data = convert_float_to_uint(composited)
            Image.fromarray(uint_data, mode="RGB").save(filename, quality=quality)
        elif is_jpeg:
            uint_data = convert_float_to_uint(self.image_data)
            Image.fromarray(uint_data, mode="RGB").save(filename, quality=quality)
        else:
            uint_data = convert_float_to_uint(self.image_data)
            mode = "RGBA" if self._has_alpha() else "RGB"
            Image.fromarray(uint_data, mode=mode).save(filename)

        return self
