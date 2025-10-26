# Architecture Overview

## Table of Contents
- [System Layers](#system-layers)
- [Data Flow](#data-flow)
- [Key Design Decisions](#key-design-decisions)
  - [Async/Await Patterns](#asyncawait-patterns)
  - [SSIM Filtering](#ssim-filtering)
  - [Tracking Windows](#tracking-windows)
  - [Configuration Management](#configuration-management)

This document provides a high-level overview of the system architecture. For detailed implementation, see the individual [module READMEs](../src/catflap_prey_detector/).

## System Layers

The system is organized into five main layers:

1. **Detection Layer** - Camera capture, YOLO object detection, and multi-object tracking
2. **Classification Layer** - Prey Detection API integration for analyzing cat images
3. **Hardware Layer** - RFID jammer control and catflap locking mechanism
4. **Notification Layer** - Telegram bot for alerts and remote control
5. **Cloud Layer** - Google Cloud Storage sync for image long term persistence

## Data Flow

1. **Frame Capture**: Camera continuously captures frames
2. **Object Detection**: YOLO11n detects cats and people in each frame
3. **Tracking**: Objects are tracked across frames to avoid duplicate processing
4. **Prey Analysis**: When a cat is detected, cropped images are queued for Prey Detection API analysis
5. **Decision**: If prey is detected, the system locks the catflap via RFID jammer
6. **Notification**: Telegram alert sent with image of the cat carrying prey
7. **Auto-unlock**: Catflap automatically unlocks after configured duration (default: 5 minutes)
8. **Cloud Sync**: Images periodically synced to Google Cloud Storage (optional)

## Key Design Decisions

### Async/Await Patterns
The system uses asyncio extensively for concurrent operations:
- Multiple Prey Detection API calls processed simultaneously (max 10 concurrent)
- Non-blocking catflap control with automatic unlock timers
- Telegram bot runs in separate thread alongside detection pipeline

### SSIM Filtering
Structural Similarity Index (SSIM) filtering prevents sending duplicate images to the API:
- Images with >90% similarity are skipped

### Tracking Windows
Time-based tracking windows prevent duplicate notifications:
- Objects tracked for 15 seconds by default
- Best quality image saved for each tracked object
- Expired objects trigger notifications

### Configuration Management
Pydantic-based configuration provides:
- Environment variable integration
- Centralized configuration in `detection/config.py`

For detailed implementation of each layer, refer to the module-specific READMEs.

