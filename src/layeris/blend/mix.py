import numpy as np
from numpy.typing import NDArray


def mix(
    base_image_data: NDArray[np.float64],
    blend_data: NDArray[np.float64],
    blend_opacity: float,
) -> NDArray[np.float64]:
    """Linearly interpolate between base and blended data by *blend_opacity*."""
    if not 0.0 <= blend_opacity <= 1.0:
        raise ValueError(f"opacity must be between 0.0 and 1.0, got {blend_opacity}")
    if blend_opacity < 1.0:
        return base_image_data * (1.0 - blend_opacity) + blend_data * blend_opacity
    return blend_data
