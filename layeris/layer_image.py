from PIL import Image
from io import BytesIO
import requests
import numpy as np
import matplotlib.colors
import json

from .utils.conversions import (
    convert_uint_to_float,
    convert_float_to_uint,
    get_rgb_float_if_hex,
)
from .utils.layers import mix
from .utils.channels import split_image_into_channels, merge_channels, channel_adjust


class LayerImage:
    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def from_url(url):
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image = LayerImage._normalize_pil_image(image)
        return LayerImage(convert_uint_to_float(np.asarray(image)))

    @staticmethod
    def from_file(file_path):
        image = Image.open(file_path)
        image = LayerImage._normalize_pil_image(image)
        return LayerImage(convert_uint_to_float(np.asarray(image)))

    @staticmethod
    def from_array(image_data):
        return LayerImage(image_data)

    # ------------------------------------------------------------------
    # PIL normalisation helper
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_pil_image(image):
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

    def __init__(self, image_data):
        # image_data is always a float32/float64 array in [0, 1]
        # shape is (H, W, 3) for RGB or (H, W, 4) for RGBA
        self.image_data = image_data.astype(np.float64)

    # ------------------------------------------------------------------
    # Alpha helpers (internal)
    # ------------------------------------------------------------------

    def _has_alpha(self):
        return self.image_data.ndim == 3 and self.image_data.shape[2] == 4

    def _get_alpha(self):
        """Return the alpha channel as (H, W, 1) or None."""
        if self._has_alpha():
            return self.image_data[:, :, 3:4]
        return None

    def _rgb(self):
        """Return a view of the RGB channels only."""
        return self.image_data[:, :, :3]

    def _reattach_alpha(self, rgb_data):
        """Combine processed RGB data with the original alpha channel (if any)."""
        alpha = self._get_alpha()
        if alpha is not None:
            return np.concatenate([rgb_data, alpha], axis=2)
        return rgb_data

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resize(self, width, height):
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

    def grayscale(self):
        gray = np.dot(self._rgb(), [0.2989, 0.5870, 0.1140])
        rgb_result = np.stack((gray,) * 3, axis=-1)
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def brightness(self, factor):
        rgb_result = np.clip(self._rgb() * (1 + factor), 0, 1)
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def contrast(self, factor):
        rgb_result = np.clip(factor * (self._rgb() - 0.5) + 0.5, 0, 1)
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def hue(self, target_hue):
        hsv = matplotlib.colors.rgb_to_hsv(self._rgb())
        hsv[:, :, 0] = target_hue
        self.image_data = self._reattach_alpha(matplotlib.colors.hsv_to_rgb(hsv))
        return self

    def saturation(self, factor):
        hsv = matplotlib.colors.rgb_to_hsv(self._rgb())
        hsv = np.clip(hsv + hsv * [0, factor, 0], 0, 1)
        self.image_data = self._reattach_alpha(matplotlib.colors.hsv_to_rgb(hsv))
        return self

    def lightness(self, factor):
        rgb = self._rgb()
        if factor > 0:
            rgb_result = rgb + (1 - rgb) * factor
        elif factor < 0:
            rgb_result = rgb + rgb * factor
        else:
            rgb_result = rgb.copy()
        self.image_data = self._reattach_alpha(rgb_result)
        return self

    def curve(self, channels="rgb", curve_points=None):
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

    def darken(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.minimum(A, blend_data)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def multiply(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = A * blend_data
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def color_burn(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.clip(np.where(B > 0, 1 - (1 - A) / B, 0), 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def linear_burn(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.clip(A + blend_data - 1, 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    # ------------------------------------------------------------------
    # Blend modes (lighten group)
    # ------------------------------------------------------------------

    def lighten(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.maximum(A, blend_data)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def screen(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = 1 - (1 - A) * (1 - B)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def color_dodge(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.where(B == 1, B, np.clip(A / (1 - B), 0, 1))
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def linear_dodge(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.clip(A + blend_data, 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    # ------------------------------------------------------------------
    # Blend modes (contrast group)
    # ------------------------------------------------------------------

    def overlay(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = np.where(A <= 0.5, 2 * A * B, 1 - 2 * (1 - A) * (1 - B))
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def soft_light(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        data01 = 2 * A * B + np.square(A) * (1 - 2 * B)
        data02 = np.sqrt(A) * (2 * B - 1) + 2 * A * (1 - B)
        result = np.where(B <= 0.5, data01, data02)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def hard_light(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        result = np.where(B <= 0.5, 2 * A * B, 1 - 2 * (1 - A) * (1 - B))
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def vivid_light(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        B = blend_data
        with np.errstate(divide="ignore", invalid="ignore"):
            color_burn = np.where(B > 0, 1 - (1 - A) / (2 * B), 0)
            color_dodge = np.where(B < 1, A / (2 * (1 - B)), 1)
        result = np.clip(np.where(B <= 0.5, color_burn, color_dodge), 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def linear_light(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)
        A = self._rgb()
        result = np.clip(A + 2 * blend_data - 1, 0, 1)
        self.image_data = self._reattach_alpha(mix(A, result, opacity))
        return self

    def pin_light(self, blend_data, opacity=1.0):
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

    def clone(self):
        return LayerImage.from_array(self.image_data.copy())

    def get_image_as_array(self):
        return self.image_data

    # ------------------------------------------------------------------
    # JSON / dict operation sequencing
    # ------------------------------------------------------------------

    def apply_from_dict(self, data):
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
            elif op_type == "darken" and hex_string is not None:
                self.darken(hex_string, opacity)
            elif op_type == "multiply" and hex_string is not None:
                self.multiply(hex_string, opacity)
            elif op_type == "color_burn" and hex_string is not None:
                self.color_burn(hex_string, opacity)
            elif op_type == "linear_burn" and hex_string is not None:
                self.linear_burn(hex_string, opacity)
            elif op_type == "lighten" and hex_string is not None:
                self.lighten(hex_string, opacity)
            elif op_type == "screen" and hex_string is not None:
                self.screen(hex_string, opacity)
            elif op_type == "color_dodge" and hex_string is not None:
                self.color_dodge(hex_string, opacity)
            elif op_type == "linear_dodge" and hex_string is not None:
                self.linear_dodge(hex_string, opacity)
            elif op_type == "overlay" and hex_string is not None:
                self.overlay(hex_string, opacity)
            elif op_type == "soft_light" and hex_string is not None:
                self.soft_light(hex_string, opacity)
            elif op_type == "hard_light" and hex_string is not None:
                self.hard_light(hex_string, opacity)
            elif op_type == "vivid_light" and hex_string is not None:
                self.vivid_light(hex_string, opacity)
            elif op_type == "linear_light" and hex_string is not None:
                self.linear_light(hex_string, opacity)
            elif op_type == "pin_light" and hex_string is not None:
                self.pin_light(hex_string, opacity)

        return self

    def apply_from_json(self, filepath):
        """Load a JSON file and apply the operation sequence it defines."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return self.apply_from_dict(data)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, filename, quality=95):
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
