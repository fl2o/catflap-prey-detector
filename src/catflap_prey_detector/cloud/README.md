# Cloud Storage Module

## Table of Contents
- [Components](#components)
  - [`storage_sync.py`](#storage_syncpy)
  - [`sync_scheduler.py`](#sync_schedulerpy)

Google Cloud Storage sync for automatic image backup and archival.

**Note:** Cloud sync is **disabled by default**. To enable it, set the `CLOUD_SYNC_ENABLED` environment variable to `true` or modify the configuration in `detection/config.py`.

## Components

### `storage_sync.py`
Core GCS upload functionality with async batch processing.

**Features:**
- Lazy-loaded GCS client and bucket
- Async file uploads with concurrent processing
- Batch uploads (configurable batch size)
- Automatic bucket access verification
- Upload statistics tracking

**Usage:**
```python
from catflap_prey_detector.cloud.storage_sync import CloudStorageSync

storage_sync = CloudStorageSync()

# Sync a directory to GCS
stats = await storage_sync.sync_directory(
    local_dir="runtime/prey_images",
    cloud_prefix="prey_images",
    file_pattern="*.jpg"
)
print(f"Uploaded: {stats['uploaded']}, Failed: {stats['failed']}")
```

### `sync_scheduler.py`
Periodic sync scheduler that runs as an async background task.

**Process:**
1. Waits for configured interval (default: 24 hours)
2. Syncs three directories to GCS:
   - `detection_images/` - YOLO detection tracking images
   - `prey_images/` - Confirmed prey detection images
   - `prey_detector_images/` - Images sent to prey detector API for analysis
3. Optionally cleans up local files after successful upload
4. Logs upload statistics
