import pytest
from pathlib import Path
from catflap_prey_detector.detection.yolo_detector import YOLODetector

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_get_class_id():
    class_id = YOLODetector.get_class_id("cat")
    
    expected_class_id = 0
    assert class_id == expected_class_id


def test_get_class_id_invalid():
    with pytest.raises(ValueError):
        YOLODetector.get_class_id("invalid_class")


def test_detect_with_image(test_images_dir):
    detector = YOLODetector()
    
    import cv2
    image_path = test_images_dir / "cat_with_prey.jpeg"
    image = cv2.imread(str(image_path))
    
    detections = detector.detect(image)
    
    assert isinstance(detections, list)
    
    has_detections = len(detections) > 0
    expected_has_detections = True
    assert has_detections == expected_has_detections
    
    cat_class_id = YOLODetector.get_class_id("cat")
    cat_detections = [d for d in detections if d.label == cat_class_id]
    
    has_cat_detection = len(cat_detections) > 0
    expected_has_cat_detection = True
    assert has_cat_detection == expected_has_cat_detection

