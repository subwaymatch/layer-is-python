import numpy as np
from numpy.typing import NDArray


def convert_uint_to_float(img_data: NDArray[np.uint8]) -> NDArray[np.float64]:
    return img_data / 255


def convert_float_to_uint(img_data: NDArray[np.float64]) -> NDArray[np.uint8]:
    return round_to_uint(img_data * 255)


def round_to_uint(img_data: NDArray[np.float64]) -> NDArray[np.uint8]:
    return np.round(img_data).astype("uint8")


def hex_to_rgb(hex_string: str) -> NDArray[np.int_]:
    return np.array(list(int(hex_string.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4)))


def hex_to_rgb_float(hex_string: str) -> NDArray[np.float64]:
    return np.array(
        list((int(hex_string.lstrip("#")[i : i + 2], 16) / 255) for i in (0, 2, 4))
    )


def get_rgb_float_if_hex(blend_data: str | NDArray[np.float64]) -> NDArray[np.float64]:
    if isinstance(blend_data, str):
        return hex_to_rgb_float(blend_data)
    return blend_data


def get_array_from_hex(hex_string: str, height: int, width: int) -> NDArray[np.float64]:
    rgb_as_float = hex_to_rgb_float(hex_string)
    return np.full((height, width, 3), rgb_as_float)
