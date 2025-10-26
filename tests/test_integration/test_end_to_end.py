import pytest
import asyncio
import cv2
import io
from pathlib import Path
from unittest.mock import AsyncMock, patch
from conftest import skip_if_no_api_key
from catflap_prey_detector.detection.detection_result import DetectionResult
from catflap_prey_detector.classification.prey_detector_api.common import load_and_prepare_image, TARGET_SIZE


@pytest.mark.asyncio
async def test_prey_detection_api_mock():
    from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey
    
    with patch('catflap_prey_detector.classification.prey_detector_api.detector.make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = False
        
        result = await detect_prey(b"fake_image_bytes")
        
        expected_is_positive = False
        assert result.is_positive == expected_is_positive


@pytest.mark.asyncio
async def test_catflap_lock_unlock_flow(mock_gpiozero):
    from catflap_prey_detector.hardware.catflap_controller import CatflapController
    from catflap_prey_detector.hardware import rfid_jammer
    
    rfid_jammer.relay = mock_gpiozero
    
    controller = CatflapController()
    controller.lock_duration_seconds = 1
    
    lock_result = await controller.lock_catflap("Test lock")
    
    expected_lock_result = True
    expected_is_locked = True
    
    assert lock_result == expected_lock_result
    assert controller.is_locked == expected_is_locked
    
    await asyncio.sleep(1.5)
    
    expected_is_locked_after = False
    assert controller.is_locked == expected_is_locked_after


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_prey_detection_with_real_api(test_images_dir):
    from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey
    
    image_path = test_images_dir / "cat_no_prey.jpeg"
    
    img_resized, _ = load_and_prepare_image(str(image_path), target_size=TARGET_SIZE, resize=True)
    
    buffer = io.BytesIO()
    img_resized.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    
    result = await detect_prey(image_bytes)
    
    expected_result_type = DetectionResult
    assert isinstance(result, expected_result_type)
    assert result.is_positive is False


PROJECT_ROOT = Path(__file__).parent.parent.parent

def test_full_detection_pipeline_without_prey_detection(test_images_dir):
    from catflap_prey_detector.detection.yolo_detector import YOLODetector
    from catflap_prey_detector.detection.tracker import DetectionTracker
    from datetime import datetime
    
    detector = YOLODetector()
    tracker = DetectionTracker(save_images=False, class_names=detector.classes_of_interest)
    
    image_path = test_images_dir / "cat_no_prey.jpeg"
    image = cv2.imread(str(image_path))
    
    detections = detector.detect(image)
    
    assert isinstance(detections, list)
    assert len(detections) > 0
    
    timestamp = datetime.now()
    _ = tracker.update(detections, image, timestamp)
    
    assert len(tracker.tracked_objects) > 0
    
    cat_class_id = YOLODetector.get_class_id("cat")
    cat_tracked = any(obj.label == cat_class_id for obj in tracker.tracked_objects.values())
    assert cat_tracked


@skip_if_no_api_key
@pytest.mark.asyncio
async def test_full_pipeline_with_prey_detection_and_catflap(test_images_dir, mock_gpiozero):
    from catflap_prey_detector.detection.yolo_detector import YOLODetector
    from catflap_prey_detector.detection.tracker import DetectionTracker
    from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey
    from catflap_prey_detector.hardware.catflap_controller import CatflapController
    from catflap_prey_detector.hardware import rfid_jammer
    from datetime import datetime
    
    rfid_jammer.relay = mock_gpiozero
    
    detector = YOLODetector()
    tracker = DetectionTracker(save_images=False, class_names=detector.classes_of_interest)
    controller = CatflapController()
    controller.lock_duration_seconds = 2
    
    image_path = test_images_dir / "cat_with_prey.jpeg"
    image = cv2.imread(str(image_path))
    
    detections = detector.detect(image)
    assert len(detections) > 0
    
    timestamp = datetime.now()
    _ = tracker.update(detections, image, timestamp)
    
    assert len(tracker.tracked_objects) > 0
    
    img_resized, _ = load_and_prepare_image(str(image_path), target_size=TARGET_SIZE, resize=True)
    
    buffer = io.BytesIO()
    img_resized.save(buffer, format='JPEG')
    image_bytes = buffer.getvalue()
    
    prey_result = await detect_prey(image_bytes)
    assert isinstance(prey_result, DetectionResult)
    assert prey_result.is_positive is True
    
    lock_result = await controller.lock_catflap("Prey detected in end-to-end test")
    
    expected_lock_result = True
    expected_is_locked = True
    assert lock_result == expected_lock_result
    assert controller.is_locked == expected_is_locked
    
    await controller.unlock_catflap()
    
    expected_is_locked_after_unlock = False
    assert controller.is_locked == expected_is_locked_after_unlock
