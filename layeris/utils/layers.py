def mix(base_image_data, blend_data, blend_opacity):
    if blend_opacity < 1.0:
        return base_image_data * (1.0 - blend_opacity) + blend_data * blend_opacity

    return blend_data
