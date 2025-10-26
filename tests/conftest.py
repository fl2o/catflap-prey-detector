"""Pytest configuration for catflap prey detector tests."""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock

src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

mock_output_device_instance = MagicMock()
mock_output_device_instance.on = MagicMock()
mock_output_device_instance.off = MagicMock()

mock_gpiozero_module = MagicMock()
mock_gpiozero_module.OutputDevice = MagicMock(return_value=mock_output_device_instance)
sys.modules['gpiozero'] = mock_gpiozero_module

mock_picamera2_module = MagicMock()
sys.modules['picamera2'] = mock_picamera2_module

mock_libcamera_module = MagicMock()
mock_libcamera_module.controls = MagicMock()
mock_libcamera_module.Transform = MagicMock()
sys.modules['libcamera'] = mock_libcamera_module


@pytest.fixture(scope="session")
def models_dir():
    """Return path to models directory."""
    return Path(__file__).parent.parent / "models"


@pytest.fixture(scope="session")
def test_images_dir():
    """Return path to test images directory."""
    return Path(__file__).parent


@pytest.fixture
def mock_gpiozero(monkeypatch):
    """Mock gpiozero module for non-Raspberry Pi systems."""
    mock_output_device = MagicMock()
    mock_module = MagicMock()
    mock_module.OutputDevice.return_value = mock_output_device
    
    monkeypatch.setitem(sys.modules, 'gpiozero', mock_module)
    
    return mock_output_device


@pytest.fixture
def mock_picamera2(monkeypatch):
    """Mock picamera2 and libcamera modules for non-Raspberry Pi systems."""
    mock_camera = MagicMock()
    mock_camera.sensor_modes = [
        {'size': (640, 480), 'bit_depth': 10},
        {'size': (1920, 1080), 'bit_depth': 10}
    ]
    
    mock_picamera2_module = MagicMock()
    mock_picamera2_module.Picamera2.return_value = mock_camera
    
    mock_libcamera_module = MagicMock()
    mock_libcamera_module.controls = MagicMock()
    mock_libcamera_module.Transform = MagicMock()
    
    monkeypatch.setitem(sys.modules, 'picamera2', mock_picamera2_module)
    monkeypatch.setitem(sys.modules, 'libcamera', mock_libcamera_module)
    
    return mock_camera


def has_prey_detection_api_key() -> bool:
    """Check if prey_detector_api_key is set."""
    return bool(os.getenv("prey_detector_api_key"))


def has_gcs_credentials() -> bool:
    """Check if GOOGLE_APPLICATION_CREDENTIALS is set."""
    return bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))


def has_telegram_credentials() -> bool:
    """Check if BOT_TOKEN and GROUP_ID are set."""
    return bool(os.getenv("BOT_TOKEN") and os.getenv("GROUP_ID"))


skip_if_no_api_key = pytest.mark.skipif(
    not has_prey_detection_api_key(),
    reason="prey_detector_api_key not set"
)

skip_if_no_gcs = pytest.mark.skipif(
    not has_gcs_credentials(),
    reason="GOOGLE_APPLICATION_CREDENTIALS not set"
)

skip_if_no_telegram = pytest.mark.skipif(
    not has_telegram_credentials(),
    reason="BOT_TOKEN or GROUP_ID not set"
)
