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


### Basic operations

#### Grayscale
```
image.grayscale()
```
![sample_grayscale](https://user-images.githubusercontent.com/1064036/66761386-e2fea380-eede-11e9-8c62-3ef88d6ee289.jpg)

### Blend mode operations

#### Darken
```
grayscale_image.darken('#3fe28f')
```
![sample_darken](https://user-images.githubusercontent.com/1064036/66762165-6b317880-eee0-11e9-960c-560d4f021aa2.jpg)

#### Multiply
```
grayscale_image.multiply('#3fe28f')
```
![sample_multiply](https://user-images.githubusercontent.com/1064036/66762301-af247d80-eee0-11e9-928d-4fa4a826f167.jpg)

#### Color Burn
```
grayscale_image.color_burn('#7fe3f8')
```
![sample_color_burn](https://user-images.githubusercontent.com/1064036/66762811-9f596900-eee1-11e9-961c-d673a6009a49.jpg)


#### Linear Burn
```
grayscale_image.linear_burn('#e1a8ff')
```
![sample_linear_burn](https://user-images.githubusercontent.com/1064036/66762820-a2ecf000-eee1-11e9-95df-6625e2da712c.jpg)

#### Lighten
```
image.lighten('#ff3ce1')
```
![sample_lighten](https://user-images.githubusercontent.com/1064036/66764586-117f7d00-eee5-11e9-96b6-e387e46d93e2.jpg)

#### Screen
```
image.screen('#e633ba')
```
![sample_screen](https://user-images.githubusercontent.com/1064036/66764718-59060900-eee5-11e9-9539-23428676b4de.jpg)

#### Color Dodge
```
image.color_dodge('#490cc7')
```
![sample_color_dodge](https://user-images.githubusercontent.com/1064036/66764854-a7b3a300-eee5-11e9-968c-cff40b1ea524.jpg)

#### Linear Dodge
```
image.linear_dodge('#490cc7')
```
![sample_linear_dodge](https://user-images.githubusercontent.com/1064036/66764998-efd2c580-eee5-11e9-9795-f56976c639b2.jpg)

#### Overlay
```
image.overlay('#ffb956')
```
![sample_overlay](https://user-images.githubusercontent.com/1064036/66765248-78e9fc80-eee6-11e9-99ff-7b1df141ac40.jpg)

#### Soft Light
```
image.soft_light('#ff3cbc')
```
![sample_soft_light](https://user-images.githubusercontent.com/1064036/66765355-b77fb700-eee6-11e9-844a-5adb3b47b9cd.jpg)

#### Hard Light
```
image.hard_light('#df5dff')
```
![sample_hard_light](https://user-images.githubusercontent.com/1064036/66765542-16453080-eee7-11e9-8a14-7fb1b6076618.jpg)

#### Vivid Light
```
image.vivid_light('#ac5b7f')
```
![sample_vivid_light](https://user-images.githubusercontent.com/1064036/66765734-818f0280-eee7-11e9-8fce-1f03a2d08675.jpg)

#### Linear Light
```
image.linear_light('#9fa500')
```
![sample_linear_light](https://user-images.githubusercontent.com/1064036/66765909-d29ef680-eee7-11e9-99ac-a088c4d2ae95.jpg)

#### Pin Light
```
image.pin_light('#005546')
```
![sample_pin_light](https://user-images.githubusercontent.com/1064036/66766030-185bbf00-eee8-11e9-998a-8c44b6d34132.jpg)


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
