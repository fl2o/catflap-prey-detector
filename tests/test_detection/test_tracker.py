import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from catflap_prey_detector.detection.tracker import DetectionTracker, TrackedObject


def test_detection_tracker_update():
    tracker = DetectionTracker(save_images=False, class_names=["cat", "person"])
    
    mock_detection = MagicMock()
    mock_detection.label = 0
    mock_detection.prob = 0.85
    mock_detection.rect = MagicMock()
    mock_detection.rect.x = 10
    mock_detection.rect.y = 10
    mock_detection.rect.w = 50
    mock_detection.rect.h = 50
    
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    timestamp = datetime.now()
    
    expired = tracker.update([mock_detection], image, timestamp)
    
    expected_expired_count = 0
    assert len(expired) == expected_expired_count
    
    expected_tracked_count = 1
    assert len(tracker.tracked_objects) == expected_tracked_count


def test_tracked_object_update():
    mock_detection = MagicMock()
    mock_detection.label = 0
    mock_detection.prob = 0.75
    mock_detection.rect = MagicMock()
    
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    timestamp = datetime.now()
    
    tracked = TrackedObject("cat_0", mock_detection, timestamp, image)
    
    expected_confidence = 0.75
    assert tracked.best_confidence == expected_confidence
    
    new_detection = MagicMock()
    new_detection.label = 0
    new_detection.prob = 0.90
    new_detection.rect = MagicMock()
    new_detection.rect.x = 10
    new_detection.rect.y = 10
    new_detection.rect.w = 50
    new_detection.rect.h = 50
    
    new_timestamp = timestamp + timedelta(seconds=1)
    tracked.update(new_detection, new_timestamp, image)
    
    expected_new_confidence = 0.90
    expected_detection_count = 2
    
    assert tracked.best_confidence == expected_new_confidence
    assert tracked.detection_count == expected_detection_count
