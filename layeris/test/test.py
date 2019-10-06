import os
import numpy as np

from layeris.layer_image import LayerImage

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'puppy.jpg')

image = LayerImage.from_file(filename)

"""
image.clone() \
    .grayscale() \
    .save('puppy_grayscale.jpg') \
    .darken('#ff0090', 0.4) \
    .save('puppy_grayscale_darken40.jpg')

image.clone() \
    .multiply('#af5def') \
    .save('puppy_multiply100.jpg')

image.clone() \
    .color_burn('#49ffe3', 0.5) \
    .save('puppy_color_burn50.jpg')

image.clone() \
    .linear_burn('#49ffe3', 0.9) \
    .save('puppy_linear_burn90.jpg')

image.clone() \
    .lighten('#b4b0cf', 0.35) \
    .save('puppy_lighten35.jpg')

image.clone() \
    .screen('#8c23a6', 1.0) \
    .save('puppy_screen100.jpg')

image.clone() \
    .color_dodge('#ba00ff', 0.7) \
    .save('puppy_color_dodge70.jpg')

image.clone() \
    .linear_dodge('#496588', 0.6) \
    .save('puppy_linear_dodge60.jpg')

image.clone() \
    .overlay(np.array([1.0, 0, 0.54]), 0.5) \
    .save('puppy_overlay50.jpg')

image.clone() \
    .soft_light('#00a2ff', 0.85) \
    .save('puppy_soft_light85.jpg')

image.clone() \
    .grayscale() \
    .hard_light('#6feb00', 0.75) \
    .save('puppy_hard_light85.jpg')

"""

image.clone() \
    .grayscale() \
    .hard_light('#6feb00', 0.75) \
    .save('puppy_hard_light85.jpg')
