# Configuration Guide

## Table of Contents
- [Required Environment Variables](#required-environment-variables)
  - [Telegram Configuration](#telegram-configuration)
  - [Prey Detection API Configuration](#prey-detection-api-configuration)
- [Optional Environment Variables](#optional-environment-variables)
  - [Google Cloud Storage (for long-term image persistence)](#google-cloud-storage-for-long-term-image-persistence)
- [Configuration File](#configuration-file)
- [Key Tunable Parameters](#key-tunable-parameters)
  - [Catflap Lock Duration](#catflap-lock-duration)
  - [YOLO Detection Classes](#yolo-detection-classes)
  - [YOLO Confidence Thresholds](#yolo-confidence-thresholds)

The system configuration is primarily managed through environment variables and the self-documented `src/catflap_prey_detector/detection/config.py` file. This guide covers the essential configuration needed to get started.

## Required Environment Variables

These must be set before running the system:

### Telegram Configuration
- **`BOT_TOKEN`** - Your Telegram bot token
  - Get from [@BotFather](https://t.me/botfather) on Telegram
  - Create a new bot with `/newbot` command
  
- **`GROUP_ID`** - Your Telegram chat/group ID
  - Start the bot and use `/where` command to get your chat ID
  - Can be a private chat or group chat ID

### Prey Detection API Configuration
  
- **`PREY_DETECTOR_API_KEY`** - API authentication key
  - Your API key for authentication

## Optional Environment Variables

### Google Cloud Storage (for long-term image persistence)

**Note:** Cloud sync is **disabled by default**. To enable it, you must:
1. Set `CLOUD_SYNC_ENABLED=true` in your environment
2. Configure the required GCS credentials below

- **`CLOUD_SYNC_ENABLED`** - Enable/disable cloud storage sync
  - Set to `true` to enable automatic image backup to Google Cloud Storage
  - Default: `false`

- **`GCS_BUCKET_NAME`** - Google Cloud Storage bucket name
  - Only needed if cloud sync is enabled
  - Default: `catflap`
  
- **`GOOGLE_APPLICATION_CREDENTIALS`** - Path to service account JSON file
  - Path to your GCS service account credentials
  - Example: `/path/to/google-sa.json`
  - Required if cloud sync is enabled

## Configuration File

The recommended way to manage environment variables is using [direnv](https://direnv.net/) with an `.envrc` file:

```bash
# .envrc
export BOT_TOKEN="your_telegram_bot_token"
export GROUP_ID="your_telegram_group_id"
export PREY_DETECTOR_API_KEY="your_api_key"

# Optional: GCS configuration (cloud sync is disabled by default)
# Uncomment the following lines to enable cloud storage sync:
# export CLOUD_SYNC_ENABLED="true"
# export GCS_BUCKET_NAME="catflap"
# export GOOGLE_APPLICATION_CREDENTIALS="./google-sa.json"
```

## Key Tunable Parameters

Most configuration has sensible defaults in `config.py`. Here are the key parameters you might want to adjust:

### Catflap Lock Duration
```python
# In detection/config.py -> CatFlapConfig
lock_time: float = 300.0  # 5 minutes (seconds)
```
How long to keep the catflap locked after detecting prey.

### YOLO Detection Classes
```python
# In detection/config.py -> YOLOConfig
classes_of_interest: list[str] = ["cat", "person"]
```
Object classes that YOLO will detect and track. The system monitors all these classes and sends notifications for detections.

### YOLO Confidence Thresholds
```python
# In detection/config.py -> YOLOConfig
class_thresholds: dict[str, float] = {"cat": 0.45, "person": 0.75}
```
Minimum confidence thresholds for each class detection. Tune it if necessary to limit false positives in your setup.

### Camera Image Orientation
```python
# In detection/config.py -> CameraConfig
vflip: bool = True   # Vertical flip (mirror vertically)
hflip: bool = True   # Horizontal flip (mirror horizontally)
```
Camera image orientation settings. Adjust these if your camera is mounted in a different orientation. Both flips are enabled by default to match the typical catflap mounting orientation.

