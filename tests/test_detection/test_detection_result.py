from catflap_prey_detector.detection.detection_result import DetectionResult


def test_positive_detection_result():
    result = DetectionResult.positive("prey detected", b"image_data")
    
    expected_is_positive = True
    expected_message = "prey detected"
    expected_image_bytes = b"image_data"
    
    assert result.is_positive == expected_is_positive
    assert result.message == expected_message
    assert result.image_bytes == expected_image_bytes


def test_negative_detection_result():
    result = DetectionResult.negative()
    
    expected_is_positive = False
    expected_message = None
    expected_image_bytes = None
    
    assert result.is_positive == expected_is_positive
    assert result.message == expected_message
    assert result.image_bytes == expected_image_bytes

