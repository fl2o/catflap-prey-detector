# Classification Module

## Table of Contents
- [Overview](#overview)
- [Structure](#structure)
  - [`prey_detector_api/` - Prey Detector API Classification](#prey_detector_api---prey-detector-api-classification)
  - [`local/` - Local Models](#local---local-models)
- [Usage](#usage)
- [Configuration](#configuration)

AI-powered classification system for prey detection analysis.

## Overview

This module provides two classification approaches:
1. **Prey detector API-based classification** - Using prey detection API for accurate prey detection
2. **Local model classification** - For offline/edge inference (future)

## Structure

### `prey_detector_api/` - Prey Detector API Classification
API-based prey detection for analyzing cat images to detect prey.

**Main Components:**
- `detector.py` - Prey detection API client integration
- `async_utils.py` - Async queue and task management for concurrent API requests
- `common.py` - Shared utilities

**Features:**
- Async API calls with retry logic
- Concurrent request processing (max 10 concurrent)
- SSIM-based duplicate filtering
- Image cropping and resizing

**API Specifications:**
- Maximum image size: 384x384 pixels
- Rate limit: 1000 calls per day
- Works with any cat, any environment, including infrared images
- Returns boolean detection result

**Custom APIs:**
By using different APIs, the Raspberry Pi can monitor for virtually any event or object. The system is flexible and extensible. For custom API endpoints or specific monitoring needs, reach out to me with your requirements.

See [Prey Detection API Documentation](../../../docs/PREY_DETECTION_API.md) for complete API details.

### `local/` - Local Models
Placeholder for future local model implementations.

## Usage

```python
from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey

# Analyze image for prey detection
result = await detect_prey(image_bytes)

if result.is_positive:
    print(f"Prey detected! {result.message}")
```

## Configuration

Prey detector tracker settings in `detection/config.py`:
- `concurrency` - Max concurrent API requests (default: 10)
- `ssim_threshold` - Image similarity threshold (default: 0.9)
- `image_size` - Analysis image dimensions (default: 384x384)
- `reset_time_window` - Time window for analysis (default: 5.0 seconds)

