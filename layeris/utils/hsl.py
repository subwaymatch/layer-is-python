import numpy as np

"""
RGB to HSL color conversion

Note that using rgb_to_hsl_arr() and hsl_to_rgb_arr() is very slow compared to matplotlib's colors.rgb_to_hsv() and colors.hsv_to_rgb(). 

You should only use the methods below if you absolutely need HSL color space
"""


def rgb_to_hsl_arr(image_data):
    return np.apply_along_axis(rgb_to_hsl, -1, image_data)


def hsl_to_rgb_arr(image_data):
    return np.apply_along_axis(hsl_to_rgb, -1, image_data)


def rgb_to_hsl(rgb_as_float):
    r, g, b = rgb_as_float
    high = max(r, g, b)
    low = min(r, g, b)
    h, s, v = ((high + low) / 2,) * 3

    if high == low:
        h = 0.0
        s = 0.0
    else:
        d = high - low
        l = (high + low) / 2
        s = d / (2 - high - low) if l > 0.5 else d / (high + low)
        h = {
            r: (g - b) / d + (6 if g < b else 0),
            g: (b - r) / d + 2,
            b: (r - g) / d + 4,
        }[high]
        h /= 6

    return [h, s, v]


def hsl_to_rgb(hsl_as_float):
    h, s, l = hsl_as_float

    def hue_to_rgb(p, q, t):
        t += 1 if t < 0 else 0
        t -= 1 if t > 1 else 0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r, g, b = l, l, l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)

    return [r, g, b]
