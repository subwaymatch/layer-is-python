import os

from layeris.layer_image import LayerImage

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'puppy.jpg')

print('hello world')

image = LayerImage.from_file(filename)

image\
    .grayscale() \
    .save('aaa.jpg')
