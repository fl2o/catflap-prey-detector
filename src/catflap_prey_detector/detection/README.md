# Detection Module

## Table of Contents
- [Overview](#overview)
- [Components](#components)
  - [`camera_manager.py`](#camera_managerpy)
  - [`yolo_detector.py`](#yolo_detectorpy)
  - [`tracker.py`](#trackerpy)
  - [`prey_detector_tracker.py`](#prey_detector_trackerpy)
  - [`detection_pipeline.py`](#detection_pipelinepy)
  - [`config.py`](#configpy)
  - [`detection_result.py`](#detection_resultpy)
  - [`fastapi_mjpeg_server.py`](#fastapi_mjpeg_serverpy)
- [Usage](#usage)
  - [Running the Detection Pipeline](#running-the-detection-pipeline)
  - [Live Camera Stream for Positioning](#live-camera-stream-for-positioning)

Real-time object detection and tracking system using YOLO and camera integration.

## Overview

This module handles the core detection pipeline:
1. Camera capture and management
2. YOLO-based object detection
3. Object tracking across frames
4. Prey detection analysis triggering
5. Image persistence

## Components

### `camera_manager.py`
Manages Picamera2 initialization, configuration, and frame capture.

### `yolo_detector.py`
YOLO11n-NCNN detector for fast object detection.

**Process:**
1. Resize input to model dimensions
2. Run NCNN inference
3. Filter by class and confidence
4. Apply NMS to remove duplicates
5. Filter by minimum detection area

### `tracker.py`
Tracks detected objects across frames to avoid duplicate notifications.

**Features:**
- IOU-based object matching
- 15-second time window
- Best image selection 
- Periodic image saving for gathering training data

### `prey_detector_tracker.py`
Manages prey detection analysis requests when cats are detected.

**Features:**
- Position-based image cropping (left/middle/right)
- SSIM-based duplicate filtering
- Async queue management for prey detection API requests
- Automatic pause during catflap lock
- Image persistence for analysis

### `detection_pipeline.py`
Main detection loop that ties everything together.

**Flow:**
1. Initialize camera and YOLO
2. Capture frame
3. Run YOLO detection
4. Update detection tracker
5. If cat detected, trigger prey detection analysis
6. Capture follow-up frames (20 frames for higher accuracy)
7. Send notifications for expired detections

### `config.py`
Comprehensive configuration management using Pydantic.

**Config Classes:**
- `CameraConfig` - Camera settings
- `YOLOConfig` - YOLO model parameters
- `TrackerConfig` - Detection tracking settings
- `PreyDetectorTrackerConfig` - Prey detection analysis settings
- `DetectionPipelineConfig` - Pipeline control flags
- `CatFlapConfig` - Lock duration settings
- `RuntimeConfig` - Directories and logging
- `CloudSyncConfig` - GCS sync parameters

### `detection_result.py`
Standardized result dataclass for prey detection outputs.

### `fastapi_mjpeg_server.py`
Standalone FastAPI server for live camera streaming.

**Features:**
- Real-time MJPEG video stream accessible via web browser
- Timestamp overlay on video feed
- 640x360 resolution for smooth streaming
- Configurable camera settings (flip, resolution)
- Thread-safe frame buffering

**Use Cases:**
- Camera positioning and alignment during hardware setup
- Field of view verification
- Focus and image quality testing
- Night vision and infrared illumination testing

## Usage

### Running the Detection Pipeline

```python
from catflap_prey_detector.detection.detection_pipeline import run_detection_pipeline

# Run the full detection pipeline
run_detection_pipeline(
    notify_telegram=True,
    save_images=False,
    prey_detection_enabled=True
)
```

### Live Camera Stream for Positioning

Before running the main detection pipeline, use the live stream server to position your camera:

```bash
uv run python -m catflap_prey_detector.detection.fastapi_mjpeg_server
```

This starts a web server at `http://<raspberry-pi-ip>:8000` that displays a real-time camera feed. Access it from any device on your network using a web browser.

**Benefits:**
- Verify the camera field of view covers the catflap entrance
- Adjust camera angle and mounting position in real-time
- Ensure proper framing before final installation
- Test infrared illumination at night
- Check focus and image quality

The stream includes a timestamp overlay and runs at 640x360 resolution for optimal performance.

