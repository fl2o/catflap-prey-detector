import pytest
import os
import io
from pathlib import Path
from conftest import skip_if_no_api_key
from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey
from catflap_prey_detector.classification.prey_detector_api.common import load_and_prepare_image, TARGET_SIZE


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_detect_prey_no_prey(test_images_dir, monkeypatch):
    monkeypatch.setenv("PREY_DETECTION_API_KEY", os.getenv("PREY_DETECTION_API_KEY"))
    
    image_path = test_images_dir / "cat_no_prey.jpeg"
    
    img_resized, _ = load_and_prepare_image(str(image_path), target_size=TARGET_SIZE, resize=True)
    
    buffer = io.BytesIO()
    img_resized.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    
    result = await detect_prey(image_bytes)
    
    expected_is_positive = False
    assert result.is_positive == expected_is_positive


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_detect_prey_with_prey(test_images_dir, monkeypatch):
    monkeypatch.setenv("PREY_DETECTION_API_KEY", os.getenv("PREY_DETECTION_API_KEY"))
    
    image_path = test_images_dir / "cat_with_prey.jpeg"
    
    img_resized, _ = load_and_prepare_image(str(image_path), target_size=TARGET_SIZE, resize=True)
    
    buffer = io.BytesIO()
    img_resized.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    
    result = await detect_prey(image_bytes)
    
    assert result.is_positive

