"""Camera management for Picamera2."""
import logging
import time
from io import BytesIO
import numpy as np
from picamera2 import Picamera2
from libcamera import controls, Transform

from catflap_prey_detector.detection.config import camera_config, CameraConfig

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages Picamera2 initialization and frame capture."""
    
    def __init__(self):
        """Initialize the camera manager.
        
        Args:
            config: Camera configuration (uses global config if None)
        """
        self.config: CameraConfig = camera_config
        self.camera: Picamera2 | None = None
        self._started = False
        
    def initialize(self) -> None:
        """Initialize and configure the camera."""
        try:
            logger.info(f"Initializing camera with resolution {self.config.resolution}")
            
            self.camera = Picamera2()
            modes = self.camera.sensor_modes
            mode = modes[self.config.mode]
            
            # Create video configuration
            camera_config = self.camera.create_video_configuration(
                main={
                    "size": self.config.resolution,
                    "format": "RGB888"
                },
                encode=None,
                display=None,
                sensor={'output_size': mode['size'], 'bit_depth': mode['bit_depth']},
                controls={
                    'FrameDurationLimits': (
                        1_000_000 // self.config.fps,  # Min frame duration in microseconds
                        1_000_000 // self.config.fps   # Max frame duration
                    )
                },
                transform=Transform(vflip=self.config.vflip, hflip=self.config.hflip)
            )
            
            self.camera.configure(camera_config)
            
            # Log configuration
            actual_config = self.camera.camera_configuration()
            logger.info(f"Camera configuration: {actual_config}")
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}", exc_info=True)
            raise
            
    def start(self) -> None:
        """Start the camera and apply settings."""
        if not self.camera:
            raise RuntimeError("Camera not initialized. Call initialize() first.")
            
        try:
            self.camera.start()
            self._started = True
            logger.info("Camera started successfully")
            
            # Set autofocus to continuous mode
            self.camera.set_controls({"AfMode": controls.AfModeEnum.Continuous})
            logger.info("Camera autofocus set to continuous mode")
            
            # Warm up period
            logger.info(f"Camera warming up for {self.config.warmup_time} seconds...")
            time.sleep(self.config.warmup_time)
            logger.info("Camera warm-up complete")
            
        except Exception as e:
            logger.error(f"Failed to start camera: {e}", exc_info=True)
            raise
            
    def capture_frame(self, name: str = "main") -> np.ndarray | None:
        """Capture a single frame from the camera.
        
        Returns:
            Captured frame as numpy array or None if capture fails
        """
        if not self._started:
            raise RuntimeError("Camera not started. Call start() first.")
            
        try:
            frame = self.camera.capture_array(name)
            return frame
        except Exception as e:
            logger.error(f"Error capturing frame: {e}", exc_info=True)
            return None
            
    def capture_image_bytes(self, name: str = "main", quality: int = 85) -> bytes | None:
        """Capture a frame and convert it to JPEG bytes.
        
        Args:
            name: The stream name to capture from
            quality: JPEG quality (1-100, default 85)
            
        Returns:
            JPEG image as bytes or None if capture/conversion fails
        """
        if not self._started:
            raise RuntimeError("Camera not started. Call start() first.")
            
        try:
            pil_image = self.camera.capture_image(name)
            
            buffer = BytesIO()
            pil_image.save(buffer, format='JPEG', quality=quality)
            buffer.seek(0)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error capturing/converting image: {e}", exc_info=True)
            return None
            
    def stop(self) -> None:
        """Stop the camera and clean up resources."""
        if self.camera and self._started:
            try:
                self.camera.stop()
                self._started = False
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}", exc_info=True)
                
    def cleanup(self) -> None:
        """Clean up camera resources."""
        self.stop()
        
        if self.camera:
            try:
                self.camera.close()
                self.camera = None
                logger.info("Camera resources cleaned up")
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}", exc_info=True)
                
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
