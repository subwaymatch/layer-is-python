from PIL import Image
import urllib
import requests
import numpy as np
import matplotlib
from .utils.conversions import convert_uint_to_float, convert_float_to_uint, round_to_uint, get_rgb_float_if_hex
from .utils.layers import mix


class LayerImage():
    @staticmethod
    def from_url(url):
        pass

    @staticmethod
    def from_file(file_path):
        image = Image.open(file_path)
        image_data = convert_uint_to_float(np.asarray(image))

        return LayerImage(image_data)

    @staticmethod
    def from_array(image_data):
        return LayerImage(image_data)

    def __init__(self, image_data):
        self.image_data = image_data

    def grayscale(self):
        self.image_data = np.dot(self.image_data[..., :3], [
                                 0.2989, 0.5870, 0.1140])

        self.image_data = np.stack(
            (self.image_data,) * 3, axis=-1)

        print(self.image_data.shape)

        return self

    def darken(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)

        result = np.minimum(self.image_data, blend_data)

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def multiply(self, blend_data, opacity=1.0):
        blend_data = get_rgb_float_if_hex(blend_data)

        result = self.image_data * blend_data

        self.image_data = mix(self.image_data, result, opacity)

        return self

    def color_burn(self, blend_data, opacity=1.0):
        return self

    def linear_burn(self, blend_data, opacity=1.0):
        return self

    def lighten(self, blend_data, opacity=1.0):
        return self

    def screen(self, blend_data, opacity=1.0):
        return self

    def color_dodge(self, blend_data, opacity=1.0):
        return self

    def linear_dodge(self, blend_data, opacity=1.0):
        return self

    def overlay(self, blend_data, opacity=1.0):
        return self

    def soft_light(self, blend_data, opacity=1.0):
        return self

    def hard_light(self, blend_data, opacity=1.0):
        return self

    def vivid_light(self, blend_data, opacity=1.0):
        return self

    def linear_light(self, blend_data, opacity=1.0):
        return self

    def pin_light(self, blend_data, opacity=1.0):
        return self

    def brightness(self, factor):
        return self

    # Legacy contrast mode
    def contrast(self, factor):
        return self

    def hue(self, target_hue):
        return self

    def saturation(self, factor):
        return self

    def lightness(self, factor):
        return self

    def curve_adjustment(self, channel='rgb', curve_points=[0, 1]):
        return self

    def clone(self):
        return LayerImage.from_array(self.image_data)

    def save(self, filename):
        pillow_image = Image.fromarray(convert_float_to_uint(self.image_data))

        pillow_image.save(filename)

        return self
