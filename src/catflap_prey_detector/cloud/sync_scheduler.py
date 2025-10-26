"""Simple cloud storage sync function."""
import asyncio
import logging
import shutil
from datetime import datetime
from pathlib import Path

from catflap_prey_detector.cloud.storage_sync import CloudStorageSync
from catflap_prey_detector.detection.config import cloud_sync_config, runtime_config

logger = logging.getLogger(__name__)


async def run_cloud_sync_loop():
    """Run periodic cloud sync in a loop."""
    storage_sync = CloudStorageSync()
    
    while True:
        await asyncio.sleep(cloud_sync_config.sync_interval_hours * 3600)
        
        start_time = datetime.now()
        logger.info(f"Starting cloud sync at {start_time}")
        
        detection_stats = await storage_sync.sync_directory(
            runtime_config.detection_images_dir,
            "detection_images", 
            "**/*.jpg"
        )
        
        prey_stats = await storage_sync.sync_directory(
            runtime_config.prey_images_dir,
            "prey_images",
            "*.jpg"
        )
        
        prey_detector_stats = await storage_sync.sync_directory(
            runtime_config.prey_detector_images_dir,
            "prey_detector_images",
            "**/*.jpg"
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        total_uploaded = detection_stats["uploaded"] + prey_stats["uploaded"] + prey_detector_stats["uploaded"]
        total_failed = detection_stats["failed"] + prey_stats["failed"] + prey_detector_stats["failed"]
        
        logger.info(f"Cloud sync completed in {duration:.1f}s: uploaded={total_uploaded}, failed={total_failed}")
        
        if cloud_sync_config.clean_local_dir and total_uploaded > 0:
            logger.info("Cleaning up synced files from local directories")
            
            detection_path = Path(runtime_config.detection_images_dir)
            if detection_path.exists():
                for subdir in detection_path.iterdir():
                    if subdir.is_dir():
                        shutil.rmtree(subdir)
                        logger.debug(f"Removed directory {subdir}")
            
            prey_path = Path(runtime_config.prey_images_dir)
            if prey_path.exists():
                for img_file in prey_path.glob("*.jpg"):
                    img_file.unlink()
                    logger.debug(f"Deleted {img_file}")
            
            prey_detector_path = Path(runtime_config.prey_detector_images_dir)
            if prey_detector_path.exists():
                for subdir in prey_detector_path.iterdir():
                    if subdir.is_dir():
                        shutil.rmtree(subdir)
                        logger.debug(f"Removed prey detector analysis directory {subdir}")
            
            logger.info(f"Cleanup completed - deleted {total_uploaded} synced files")