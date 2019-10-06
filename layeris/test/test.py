import os

from layeris.layer_image import LayerImage

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'puppy.jpg')

print('hello world')

image = LayerImage.from_file(filename)

image\
    .multiply('#65ebff', 0.36) \
    .save('puppy_multiply_36.jpg') \
