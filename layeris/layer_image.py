"""High level image manipulation helpers."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from typing import Sequence, Union

import numpy as np
import requests
from PIL import Image
from matplotlib import colors as mpl_colors

from .utils.channels import channel_adjust, merge_channels, split_image_into_channels
from .utils.conversions import convert_float_to_uint, convert_uint_to_float, get_rgb_float_if_hex
from .utils.layers import mix


class LayerImage:
    """A convenience wrapper around a float RGB numpy array."""

    _HEX_METHODS = {
        "darken": "darken",
        "multiply": "multiply",
        "color_burn": "color_burn",
        "linear_burn": "linear_burn",
        "lighten": "lighten",
        "screen": "screen",
        "color_dodge": "color_dodge",
        "linear_dodge": "linear_dodge",
        "overlay": "overlay",
        "soft_light": "soft_light",
        "hard_light": "hard_light",
        "vivid_light": "vivid_light",
        "linear_light": "linear_light",
        "pin_light": "pin_light",
    }

    _FACTOR_METHODS = {
        "brightness": "brightness",
        "contrast": "contrast",
        "saturation": "saturation",
        "lightness": "lightness",
    }

    def __init__(self, image_data: np.ndarray):
        self.image_data = self._coerce_image_data(image_data)

    @classmethod
    def from_url(cls, url: str, *, timeout: int = 30) -> "LayerImage":
        """Create a :class:`LayerImage` from an image URL."""

        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        try:
            return cls.from_pillow_image(image)
        finally:
            image.close()

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "LayerImage":
        """Create a :class:`LayerImage` from a local file."""

        with Image.open(file_path) as image:
            return cls.from_pillow_image(image)

    @classmethod
    def from_pillow_image(cls, image: Image.Image) -> "LayerImage":
        """Create a :class:`LayerImage` from a :mod:`PIL` image instance."""

        if image.mode != "RGB":
            image = image.convert("RGB")
        image_data = convert_uint_to_float(np.asarray(image))
        return cls(image_data)

    @classmethod
    def from_array(cls, image_data: np.ndarray) -> "LayerImage":
        """Create a :class:`LayerImage` from a numpy array."""

        return cls(image_data)

    @staticmethod
    def _coerce_image_data(image_data: np.ndarray) -> np.ndarray:
        array = np.asarray(image_data)
        if array.ndim != 3 or array.shape[2] < 3:
            raise ValueError("LayerImage expects an array with shape (H, W, 3+)")

        if array.shape[2] > 3:
            array = array[:, :, :3]

        if np.issubdtype(array.dtype, np.integer):
            array = convert_uint_to_float(array)
        else:
            array = np.array(array, dtype=np.float32, copy=True)

        return np.clip(array, 0.0, 1.0)

    def grayscale(self) -> "LayerImage":
        self.image_data = np.dot(self.image_data[..., :3], [
                                 0.2989, 0.5870, 0.1140])

        self.image_data = np.stack(
            (self.image_data,) * 3, axis=-1)

        return self

    def darken(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        result = np.minimum(self.image_data, blend_data)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def multiply(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        result = self.image_data * blend_data

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def color_burn(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.clip(np.where(B > 0, 1 - (1 - A) / B, 0), 0, 1)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def linear_burn(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        result = np.clip(A + B - 1, 0, 1)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def lighten(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        result = np.maximum(self.image_data, blend_data)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def screen(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        result = 1 - (1 - A) * (1 - B)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def color_dodge(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.where(B == 1, B, np.clip(A / (1 - B), 0, 1))

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def linear_dodge(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        result = np.clip(A + B, 0, 1)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def overlay(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        data01 = (2 * A) * B
        data02 = 1 - 2 * (1 - A) * (1 - B)

        result = np.where(A <= 0.5, data01, data02)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def soft_light(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        data01 = 2 * A * B + np.square(A) * (1 - 2 * B)
        data02 = np.sqrt(A) * (2 * B - 1) + (2 * A) * (1 - B)

        result = np.where(blend_data <= 0.5, data01, data02)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def hard_light(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        data01 = (2 * A) * B
        data02 = 1 - 2 * (1 - A) * (1 - B)

        result = np.where(blend_data <= 0.5, data01, data02)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def vivid_light(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        with np.errstate(divide="ignore", invalid="ignore"):
            image_color_burn = np.where(B > 0, 1 - (1 - A) / (2 * B), 0)
            image_color_dodge = np.where(B < 1, A / (2 * (1 - B)), 1)

        result = np.clip(
            np.where(B <= 0.5, image_color_burn, image_color_dodge), 0, 1)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def linear_light(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.clip(A + 2 * B - 1, 0, 1)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def pin_light(self, blend_data: Union[str, Sequence[float]], opacity: float = 1.0) -> "LayerImage":
        blend_data = get_rgb_float_if_hex(blend_data)

        A = self.image_data
        B = blend_data

        with np.errstate(divide="ignore", invalid="ignore"):
            result = np.clip(np.where(A < 2 * B - 1, 2 * B - 1,
                                      np.where(A > 2 * B, 2 * B, A)), 0, 1)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def brightness(self, factor: float) -> "LayerImage":
        self.image_data = np.clip(self.image_data * (1 + factor), 0, 1)

        return self

    def contrast(self, factor: float) -> "LayerImage":
        self.image_data = np.clip(factor * (self.image_data - 0.5) + 0.5, 0, 1)

        return self

    def hue(self, target_hue: float) -> "LayerImage":
        image_hsv_data = mpl_colors.rgb_to_hsv(self.image_data)
        image_hsv_data[:, :, 0] = target_hue

        self.image_data = mpl_colors.hsv_to_rgb(image_hsv_data)

        return self

    def saturation(self, factor: float) -> "LayerImage":
        image_hsv_data = mpl_colors.rgb_to_hsv(self.image_data)
        image_hsv_data = np.clip(
            image_hsv_data + image_hsv_data * [0, factor, 0], 0, 1)

        self.image_data = mpl_colors.hsv_to_rgb(image_hsv_data)

        return self

    def lightness(self, factor: float) -> "LayerImage":
        if factor > 0:
            self.image_data = self.image_data + \
                ((1 - self.image_data) * factor)
        elif factor < 0:
            self.image_data = self.image_data + (self.image_data * factor)

        self.image_data = np.clip(self.image_data, 0, 1)

        return self

    def curve(self, channels: str = 'rgb', curve_points: Sequence[float] = (0, 1)) -> "LayerImage":
        r, g, b = split_image_into_channels(self.image_data)

        if 'r' in channels:
            r = channel_adjust(r, curve_points)
        if 'g' in channels:
            g = channel_adjust(g, curve_points)
        if 'b' in channels:
            b = channel_adjust(b, curve_points)

        self.image_data = merge_channels(r, g, b)

        return self

    def clone(self) -> "LayerImage":
        return LayerImage.from_array(self.image_data.copy())

    def get_image_as_array(self, *, copy: bool = True) -> np.ndarray:
        return self.image_data.copy() if copy else self.image_data

    def apply_from_json(self, filepath: Union[str, Path]) -> "LayerImage":
        with open(filepath, 'r', encoding='utf-8') as content_file:
            json_obj = json.load(content_file)
        operations = json_obj.get('operations', [])

        for op in operations:
            op_type = op.get('type')
            if op_type == 'grayscale':
                self.grayscale()
            elif op_type in self._HEX_METHODS:
                hex_string = op.get('hex')
                if hex_string is None:
                    raise ValueError(f"Operation '{op_type}' requires a 'hex' value")
                opacity = float(op.get('opacity', 1.0))
                getattr(self, self._HEX_METHODS[op_type])(hex_string, opacity)
            elif op_type in self._FACTOR_METHODS:
                factor = op.get('factor')
                if factor is None:
                    raise ValueError(f"Operation '{op_type}' requires a 'factor' value")
                getattr(self, self._FACTOR_METHODS[op_type])(float(factor))
            elif op_type == 'hue':
                if 'hue' not in op:
                    raise ValueError("Operation 'hue' requires a 'hue' value")
                self.hue(float(op['hue']))
            elif op_type == 'curve':
                channels = op.get('channels')
                curve_points = op.get('curve_points')
                if channels is None or curve_points is None:
                    raise ValueError("Operation 'curve' requires 'channels' and 'curve_points'")
                self.curve(str(channels), curve_points)

        return self

    def save(self, filename: Union[str, Path], quality: int = 75) -> "LayerImage":
        pillow_image = Image.fromarray(convert_float_to_uint(self.image_data))
        pillow_image.save(filename, quality=quality)

        return self
