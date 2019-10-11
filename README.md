<p align="center">
<img src="https://user-images.githubusercontent.com/1064036/66263389-f9e12e00-e82c-11e9-87d4-1b792fb16c7b.png">
</p>

# Layer.is
A library that supports all blend modes in Photoshop, brightness, contrast, hue, saturation, lightness adjustments, and curve adjustments on separate RGB channels. 

## Why use Layer.is? 

- Supports all frequently used blend modes in Photoshop
- Chain operations (like jQuery)
- Straightforward API to manipulate images
- Load sequence of operations from JSON
- Can apply curve adjustment selectively to RGB channels

## Requirements
Layer.is requires Python 3.6 or higher. 

## Quick Start

### Installation
Install layer-is from PyPI repository. 
```
$ pip install layer-is
```

### Load/Save an image

#### Loading an image from file
```
from layeris.layer_image import LayerImage

image = LayerImage.from_file('/path/to/your/image.jpg')
```

#### Loading an image from URL
```
from layeris.layer_image import LayerImage

image = LayerImage.from_url('https://your-image-url')
```

#### Saving an image
```
image.save('output.jpg')
```

You can also specify the image quality between 0 - 100 by passing in the optional `quality` parameter. By default, `quality` is set to 75. 
```
image.save('output.jpg', 90)
```

### Blend mode operations



### Other utility methods

#### Getting image as NumPy array
```
image.get_image_as_array()
```
This will return a NumPy array with shape (`height`, `width`, 3). Note that the each pixel value is 


#### Cloning a LayerImage instance
```
image.clone()
```


## Roadmap

- Add resizing capabilities using scikit-image.
- Imitate Photoshop's auto brightness & auto contrast features
- Add presets of filters
