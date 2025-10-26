"""Configuration management for the object detection system with prey detection analysis."""
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class CameraConfig(BaseSettings):
    """Camera configuration settings."""
    resolution: tuple[int, int] = Field(default=(640, 360), description="Camera resolution (width, height)")
    mode: int = Field(default=1, description="Camera sensor mode")
    fps: int = Field(default=30, description="Camera frames per second")
    warmup_time: float = Field(default=2.0, description="Camera warmup time in seconds")
    vflip: bool = Field(default=True, description="Vertical flip (mirror vertically)")
    hflip: bool = Field(default=True, description="Horizontal flip (mirror horizontally)")
    
    @field_validator('resolution')
    @classmethod
    def validate_resolution(cls, v: tuple[int, int]) -> tuple[int, int]:
        if len(v) != 2 or v[0] <= 0 or v[1] <= 0:
            raise ValueError("Resolution must be a tuple of two positive integers")
        return v


class YOLOConfig(BaseSettings):
    """YOLO model configuration."""
    model_path: str = Field(
        default=str(PROJECT_ROOT / "models" / "yolo11n_ncnn_model_384_640" / "model.ncnn"),
        description="Base path to YOLO model files (without extension)"
    )
    
    @property
    def model_param_path(self) -> str:
        """Get the path to the YOLO model param file."""
        return f"{self.model_path}.param"
    
    @property
    def model_bin_path(self) -> str:
        """Get the path to the YOLO model bin file."""
        return f"{self.model_path}.bin"
    image_size: tuple[int, int] = Field(default=(384, 640), description="Input image size for YOLO model")
    class_thresholds: dict[str, float] = Field(
        default={"cat": 0.45, "person": 0.75}, 
        description="Confidence thresholds per class"
    )
    iou_threshold: float = Field(default=0.02, description="IOU threshold for NMS")

    classes_of_interest: list[str] = Field(
        default=["cat", "person"],
        description="Classes to detect"
    )
    min_detection_area: float = Field(default=1*1, description="Minimum detection area for detections in pixels^2, to limit false positives")
    
    @field_validator('class_thresholds')
    @classmethod
    def validate_class_thresholds(cls, v: dict[str, float]) -> dict[str, float]:
        for class_name, threshold in v.items():
            if not 0 <= threshold <= 1:
                raise ValueError(f"Threshold for class '{class_name}' must be between 0 and 1")
        return v
    
    @field_validator('iou_threshold')
    @classmethod
    def validate_threshold(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return v


class TrackerConfig(BaseSettings):
    """Configuration for detection and prey detection analysis trackers."""
    detection_time_window: float = Field(default=15.0, description="Time window for detection tracking (seconds)")
    detection_iou_threshold: float = Field(default=0.0, description="IOU threshold for detection matching")
    save_frequency: float = Field(default=0.2, description="Frequency of saving images (0-1)")

class DetectionPipelineConfig(BaseSettings):
    """Main configuration for the detector system."""
    prey_detection_trigger_class: str = Field(default="cat", description="Object class that triggers prey detection analysis (e.g., 'cat', 'person', 'dog')")
    prey_detection_enabled: bool = Field(default=True, description="Whether prey detection analysis is enabled")
    telegram_enabled: bool = Field(default=True, description="Whether telegram notifications are enabled")
    save_images: bool = Field(default=True, description="Whether to save detection images")
    cloud_sync_enabled: bool = Field(default=False, description="Whether to enable cloud storage sync")
    detection_followup_frames: int = Field(default=20, description="Number of frames to follow up on after detection of class of interest (to augment fps)")

    @property
    def prey_detection_trigger_class_id(self) -> int:
        """Get the class ID for the prey detection trigger class from YOLO config."""
        return yolo_config.classes_of_interest.index(self.prey_detection_trigger_class)
    
class PreyDetectorTrackerConfig(BaseSettings):
    """Configuration for the prey detector tracker."""
    reset_time_window: float = Field(default=5.0, description="Time window for prey detection analysis tracking (seconds)")
    image_size: tuple[int, int] | None = Field(default=(384, 384), description="Image size for prey detection analysis, None for the camera size")
    concurrency: int = Field(default=10, description="Maximum number of concurrent prey detection API requests")
    ssim_threshold: float = Field(default=0.9, description="SSIM threshold for image similarity comparison")
    save_images: bool = Field(default=True, description="Whether to save images for prey detection analysis")

class CatFlapConfig(BaseSettings):
    """Configuration for cat flap control."""
    lock_time: float = Field(default=300.0, description="Time to lock the cat flap after prey detection (seconds)")

class PreyDetectionAPIConfig(BaseSettings):
    """Configuration for prey detection API."""
    api_url: str = Field(default="https://prey-detection.florian-mutel.workers.dev", description="Prey detection API endpoint URL")
    prey_detector_api_key: str | None = Field(default=None, description="API key for prey detection service")

class RuntimeConfig(BaseSettings):
    """Configuration for logging."""
    log_level: str = Field(default="INFO", description="Logging level")
    root_dir: str = Field(default="runtime", description="Root directory for runtime files")
    log_dir: str = Field(default="runtime/logs", description="Logging directory")
    log_file: str = Field(default="runtime/logs/main_app.log", description="Logging file")
    detection_images_dir: str = Field(default="runtime/detection_images", description="Detection images directory")
    prey_images_dir: str = Field(default="runtime/prey_images", description="Prey images directory")
    prey_detector_images_dir: str = Field(default="runtime/prey_detector_images", description="Prey detector analysis images directory")


class CloudSyncConfig(BaseSettings):
    """Configuration for cloud storage sync."""
    bucket_name: str = Field(default="catflap", description="GCS bucket name")
    sync_interval_hours: float = Field(default=24.0, description="Hours between sync operations")
    upload_batch_size: int = Field(default=50, description="Number of files to upload in batch")
    clean_local_dir: bool = Field(default=True, description="Whether to clean local directories after sync")
    
camera_config = CameraConfig()
yolo_config = YOLOConfig()
tracker_config = TrackerConfig()
detector_config = DetectionPipelineConfig()
prey_detector_tracker_config = PreyDetectorTrackerConfig()
catflap_config = CatFlapConfig()
prey_detection_api_config = PreyDetectionAPIConfig()
runtime_config = RuntimeConfig()
cloud_sync_config = CloudSyncConfig()