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

The descriptions for each blend mode operation are copied from [https://helpx.adobe.com/photoshop/using/blending-modes.html](https://helpx.adobe.com/photoshop/using/blending-modes.html).

#### Darken
Looks at the color information in each channel and selects the base or blend color—whichever is darker—as the result color. Pixels lighter than the blend color are replaced, and pixels darker than the blend color do not change.
```
grayscale_image.darken('#3fe28f')
```
![sample_darken](https://user-images.githubusercontent.com/1064036/66762165-6b317880-eee0-11e9-960c-560d4f021aa2.jpg)

#### Multiply
Looks at the color information in each channel and multiplies the base color by the blend color. The result color is always a darker color. Multiplying any color with black produces black. Multiplying any color with white leaves the color unchanged. When you’re painting with a color other than black or white, successive strokes with a painting tool produce progressively darker colors. The effect is similar to drawing on the image with multiple marking pens.
```
grayscale_image.multiply('#3fe28f')
```
![sample_multiply](https://user-images.githubusercontent.com/1064036/66762301-af247d80-eee0-11e9-928d-4fa4a826f167.jpg)

#### Color Burn
Looks at the color information in each channel and darkens the base color to reflect the blend color by increasing the contrast between the two. Blending with white produces no change.
```
grayscale_image.color_burn('#7fe3f8')
```
![sample_color_burn](https://user-images.githubusercontent.com/1064036/66762811-9f596900-eee1-11e9-961c-d673a6009a49.jpg)


#### Linear Burn
Looks at the color information in each channel and darkens the base color to reflect the blend color by decreasing the brightness. Blending with white produces no change.
```
grayscale_image.linear_burn('#e1a8ff')
```
![sample_linear_burn](https://user-images.githubusercontent.com/1064036/66762820-a2ecf000-eee1-11e9-95df-6625e2da712c.jpg)

#### Lighten
Looks at the color information in each channel and selects the base or blend color—whichever is lighter—as the result color. Pixels darker than the blend color are replaced, and pixels lighter than the blend color do not change.
```
image.lighten('#ff3ce1')
```
![sample_lighten](https://user-images.githubusercontent.com/1064036/66764586-117f7d00-eee5-11e9-96b6-e387e46d93e2.jpg)

#### Screen
Looks at each channel’s color information and multiplies the inverse of the blend and base colors. The result color is always a lighter color. Screening with black leaves the color unchanged. Screening with white produces white. The effect is similar to projecting multiple photographic slides on top of each other.
```
image.screen('#e633ba')
```
![sample_screen](https://user-images.githubusercontent.com/1064036/66764718-59060900-eee5-11e9-9539-23428676b4de.jpg)

#### Color Dodge
Looks at the color information in each channel and brightens the base color to reflect the blend color by decreasing contrast between the two. Blending with black produces no change.
```
image.color_dodge('#490cc7')
```
![sample_color_dodge](https://user-images.githubusercontent.com/1064036/66764854-a7b3a300-eee5-11e9-968c-cff40b1ea524.jpg)

#### Linear Dodge
Looks at the color information in each channel and brightens the base color to reflect the blend color by increasing the brightness. Blending with black produces no change.
```
image.linear_dodge('#490cc7')
```
![sample_linear_dodge](https://user-images.githubusercontent.com/1064036/66764998-efd2c580-eee5-11e9-9795-f56976c639b2.jpg)

#### Overlay
Multiplies or screens the colors, depending on the base color. Patterns or colors overlay the existing pixels while preserving the highlights and shadows of the base color. The base color is not replaced, but mixed with the blend color to reflect the lightness or darkness of the original color.
```
image.overlay('#ffb956')
```
![sample_overlay](https://user-images.githubusercontent.com/1064036/66765248-78e9fc80-eee6-11e9-99ff-7b1df141ac40.jpg)

#### Soft Light
Darkens or lightens the colors, depending on the blend color. The effect is similar to shining a diffused spotlight on the image. If the blend color (light source) is lighter than 50% gray, the image is lightened as if it were dodged. If the blend color is darker than 50% gray, the image is darkened as if it were burned in. Painting with pure black or white produces a distinctly darker or lighter area, but does not result in pure black or white.
```
image.soft_light('#ff3cbc')
```
![sample_soft_light](https://user-images.githubusercontent.com/1064036/66765355-b77fb700-eee6-11e9-844a-5adb3b47b9cd.jpg)

#### Hard Light
Multiplies or screens the colors, depending on the blend color. The effect is similar to shining a harsh spotlight on the image. If the blend color (light source) is lighter than 50% gray, the image is lightened, as if it were screened. This is useful for adding highlights to an image. If the blend color is darker than 50% gray, the image is darkened, as if it were multiplied. This is useful for adding shadows to an image. Painting with pure black or white results in pure black or white.
```
image.hard_light('#df5dff')
```
![sample_hard_light](https://user-images.githubusercontent.com/1064036/66765542-16453080-eee7-11e9-8a14-7fb1b6076618.jpg)

#### Vivid Light
Burns or dodges the colors by increasing or decreasing the contrast, depending on the blend color. If the blend color (light source) is lighter than 50% gray, the image is lightened by decreasing the contrast. If the blend color is darker than 50% gray, the image is darkened by increasing the contrast.
```
image.vivid_light('#ac5b7f')
```
![sample_vivid_light](https://user-images.githubusercontent.com/1064036/66765734-818f0280-eee7-11e9-8fce-1f03a2d08675.jpg)

#### Linear Light
Burns or dodges the colors by decreasing or increasing the brightness, depending on the blend color. If the blend color (light source) is lighter than 50% gray, the image is lightened by increasing the brightness. If the blend color is darker than 50% gray, the image is darkened by decreasing the brightness.
```
image.linear_light('#9fa500')
```
![sample_linear_light](https://user-images.githubusercontent.com/1064036/66765909-d29ef680-eee7-11e9-99ac-a088c4d2ae95.jpg)

#### Pin Light
Replaces the colors, depending on the blend color. If the blend color (light source) is lighter than 50% gray, pixels darker than the blend color are replaced, and pixels lighter than the blend color do not change. If the blend color is darker than 50% gray, pixels lighter than the blend color are replaced, and pixels darker than the blend color do not change. This is useful for adding special effects to an image.
```
image.pin_light('#005546')
```
![sample_pin_light](https://user-images.githubusercontent.com/1064036/66766030-185bbf00-eee8-11e9-998a-8c44b6d34132.jpg)

### Non-blend mode operations

#### Brightness

Please note that this operation has yet to discover the exact algorithm (formula) used by Photoshop. However, the method used here is very close and extremely fast. 

```
image.brightness(0.2)
```


#### Contrast
```
image.contrast(1.15)
```

#### Hue
```
image.hue(0.2)
```

#### Saturation
```
image.saturation(-0.5)
```

#### Lightness
```
image.lightness(-0.8)
```

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
