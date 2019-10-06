import os
import sys
import numpy as np
from pathlib import Path

from layeris.layer_image import LayerImage

dirname = os.path.dirname(__file__)

files = ['puppy.jpg', 'woman.jpg', 'light_trace.jpg', 'hong_kong.jpg']

for filename in files:
    filepath = os.path.join(dirname, filename)

    file_save_prefix = os.path.splitext(filename)[0]

    image = LayerImage.from_file(filepath)

    image.clone() \
        .grayscale() \
        .save(f'{file_save_prefix}_grayscale.jpg')\
        .darken('#ff0090', 0.4) \
        .save(f'{file_save_prefix}_grayscale_darken40.jpg')

    image.clone() \
        .multiply('#af5def') \
        .save(f'{file_save_prefix}_multiply100.jpg')

    image.clone() \
        .color_burn('#49ffe3', 0.5) \
        .save(f'{file_save_prefix}_color_burn50.jpg')

    image.clone() \
        .linear_burn('#49ffe3', 0.9) \
        .save(f'{file_save_prefix}_linear_burn90.jpg')

    image.clone() \
        .lighten('#b4b0cf', 0.35) \
        .save(f'{file_save_prefix}_lighten35.jpg')

    image.clone() \
        .screen('#8c23a6', 1.0) \
        .save(f'{file_save_prefix}_screen100.jpg')

    image.clone() \
        .color_dodge('#ba00ff', 0.7) \
        .save(f'{file_save_prefix}_color_dodge70.jpg')

    image.clone() \
        .linear_dodge('#496588', 0.6) \
        .save(f'{file_save_prefix}_linear_dodge60.jpg')

    image.clone() \
        .overlay(np.array([1.0, 0, 0.54]), 0.5) \
        .save(f'{file_save_prefix}_overlay50.jpg')

    image.clone() \
        .soft_light('#00a2ff', 0.85) \
        .save(f'{file_save_prefix}_soft_light85.jpg')

    image.clone() \
        .grayscale() \
        .hard_light('#6feb00', 0.75) \
        .save(f'{file_save_prefix}_hard_light85.jpg')

    image.clone() \
        .grayscale() \
        .vivid_light('#b4ff00', 0.80) \
        .save(f'{file_save_prefix}_vivid_light80.jpg')

    image.clone() \
        .linear_light('#c853ff', 0.70) \
        .save(f'{file_save_prefix}_linear_light70.jpg')

    image.clone() \
        .grayscale() \
        .pin_light('#c853ff', 0.70) \
        .save(f'{file_save_prefix}_pin_light70.jpg')

    image.clone() \
        .brightness(0.3) \
        .save(f'{file_save_prefix}_brightness30.jpg')

    image.clone() \
        .contrast(1.15) \
        .save(f'{file_save_prefix}_contrast115.jpg')

    image.clone() \
        .hue(0.2) \
        .save(f'{file_save_prefix}_hue.jpg')

    image.clone() \
        .saturation(-0.5) \
        .save(f'{file_save_prefix}_desaturate.jpg')

    image.clone() \
        .saturation(0.3) \
        .save(f'{file_save_prefix}_saturate.jpg')

    image.clone() \
        .lightness(-0.8) \
        .save(f'{file_save_prefix}_lightness_negative80.jpg')

    image.clone() \
        .lightness(0.3) \
        .save(f'{file_save_prefix}_lightness30.jpg')

    image.clone() \
        .curve('r', [0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]) \
        .save(f'{file_save_prefix}_curve_red_boost.jpg')
