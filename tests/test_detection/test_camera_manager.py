import pytest
import numpy as np
from unittest.mock import MagicMock, patch


def test_camera_manager_initialize():
    with patch('catflap_prey_detector.detection.camera_manager.Picamera2') as mock_picamera2_class:
        mock_camera = MagicMock()
        mock_camera.sensor_modes = [
            {'size': (640, 480), 'bit_depth': 10},
            {'size': (1920, 1080), 'bit_depth': 10}
        ]
        mock_picamera2_class.return_value = mock_camera
        
        from catflap_prey_detector.detection.camera_manager import CameraManager
        
        manager = CameraManager()
        manager.initialize()
        
        expected_camera_not_none = True
        assert (manager.camera is not None) == expected_camera_not_none


def test_camera_manager_capture_frame():
    with patch('catflap_prey_detector.detection.camera_manager.Picamera2') as mock_picamera2_class:
        mock_camera = MagicMock()
        mock_camera.sensor_modes = [
            {'size': (640, 480), 'bit_depth': 10},
            {'size': (1920, 1080), 'bit_depth': 10}
        ]
        mock_camera.capture_array.return_value = np.zeros((360, 640, 3), dtype=np.uint8)
        mock_picamera2_class.return_value = mock_camera
        
        from catflap_prey_detector.detection.camera_manager import CameraManager
        
        manager = CameraManager()
        manager.initialize()
        manager.start()
        
        frame = manager.capture_frame()
        
        expected_shape = (360, 640, 3)
        assert frame.shape == expected_shape

