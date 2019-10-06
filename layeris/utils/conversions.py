from PIL import Image
import numpy as np


def convert_uint_to_float(img_data):
    return img_data / 255


def convert_float_to_uint(img_data):
    return round_to_uint(img_data * 255)


def round_to_uint(img_data):
    return np.round(img_data).astype('uint8')


def hex_to_rgb(hex_string):
    return np.array(list(int(hex_string.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)))


def hex_to_rgb_float(hex_string):
    return np.array(list((int(hex_string.lstrip('#')[i:i + 2], 16) / 255) for i in (0, 2, 4)))


def get_rgb_float_if_hex(blend_data):
    if isinstance(blend_data, str):
        return hex_to_rgb_float(blend_data)

    return blend_data


def get_array_from_hex(hex_string, height, width):
    rgb_as_float = hex_to_rgb_float(hex_string)
    return np.full((height, width, 3), rgb_as_float)
