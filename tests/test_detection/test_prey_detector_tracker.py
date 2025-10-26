import pytest
import numpy as np
from catflap_prey_detector.detection.prey_detector_tracker import crop_image


@pytest.mark.parametrize("position,expected_start_x", [
    ("left", 0),
    ("middle", 45),
    ("right", 90),
])
def test_crop_image(position, expected_start_x):
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    crop_width = 10
    
    cropped = crop_image(image, position, crop_width)
    
    expected_shape = (100, 10, 3)
    assert cropped.shape == expected_shape


def test_crop_image_left_position():
    image = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
    crop_width = 50
    
    cropped = crop_image(image, "left", crop_width)
    
    expected_width = 50
    assert cropped.shape[1] == expected_width
    assert np.array_equal(cropped, image[:, 0:50])

