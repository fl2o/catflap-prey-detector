from __future__ import annotations
from typing import Literal
import asyncio
import logging
import cv2
import numpy as np
import os
import uuid
from datetime import datetime
from catflap_prey_detector.classification.prey_detector_api.async_utils import async_consumer_with_task_group_and_result_processor, async_consumer_queue
from catflap_prey_detector.classification.prey_detector_api.detector import detect_prey
from catflap_prey_detector.notifications.telegram_bot import notify_event_async
from catflap_prey_detector.hardware.catflap_controller import detection_pauser
from catflap_prey_detector.detection.config import prey_detector_tracker_config, runtime_config
from catflap_prey_detector.detection.detection_result import DetectionResult
from skimage.metrics import structural_similarity as ssim

logger = logging.getLogger(__name__)


def crop_image(image: np.ndarray, position: str, crop_width: int) -> np.ndarray:
    """Crop image horizontally based on position.
    
    Args:
        image: Input image array
        position: Crop position - "left", "right", or "middle"
        crop_width: Width of the cropped image
        
    Returns:
        Cropped image array
    """
    height, width = image.shape[:2]
    
    if position == "left":
        start_x = 0
    elif position == "right":
        start_x = max(0, width - crop_width)
    else:  # middle
        start_x = max(0, (width - crop_width) // 2)
    
    end_x = min(width, start_x + crop_width)
    start_x = max(0, end_x - crop_width)
    
    return image[:, start_x:end_x]


async def process_detection_results(results: list[DetectionResult]) -> None:
    """
    Process a list of detection results and trigger notifications for positive detections.
    
    Args:
        results: List of DetectionResult objects from detect_prey coroutine calls
    """
    logger.info(f"Processing {len(results)=} detection results")
    
    first_positive_result = _get_positive_results(results)
    
    if first_positive_result is None:
        logger.info("No positive detections found in results")
        return
        
    await _send_notification(first_positive_result)


def _get_positive_results(results: list[DetectionResult]) -> DetectionResult | None:
    """Filter out negative results, keeping only positive detections."""
    return next((result for result in results if result.is_positive), None)


async def _send_notification(result: DetectionResult) -> None:
    """Send notification for a single detection result."""
    message, image_bytes = result.message, result.image_bytes
    await notify_event_async(message, image_bytes)


class PreyDetectorTracker:
    """Tracks object detections over time to spawn prey detection analysis tasks"""
    
    def __init__(self, prey_detection_enabled: bool = True) :
        self.time_window = prey_detector_tracker_config.reset_time_window
        self.thread_timeout = prey_detector_tracker_config.reset_time_window + 1
        self.concurrency = prey_detector_tracker_config.concurrency
        self.detector_task: asyncio.Future | None = None
        self.prey_detection_enabled = prey_detection_enabled
        self.previous_image: np.ndarray | None = None
        self.ssim_threshold = prey_detector_tracker_config.ssim_threshold
        self.save_images = prey_detector_tracker_config.save_images
        self.uuid = uuid.uuid4()
        self._next_id = 0
        
        logger.debug(f"PreyDetectorTracker {self.uuid=}")
    
    def update(self, trigger_object_position: Literal["left", "middle", "right"] | None, image_array: np.ndarray) -> None:
        if not self.prey_detection_enabled:
            logger.info("Prey detection is disabled")
            return


        if trigger_object_position:
            from catflap_prey_detector.main import MAIN_LOOP
            if MAIN_LOOP is None:
                logger.error("MAIN_LOOP is not initialized. Cannot schedule prey detection analysis task.")
            else:
                if self.detector_task is None or self.detector_task.done():
                    self.detector_task = asyncio.run_coroutine_threadsafe(
                        async_consumer_with_task_group_and_result_processor(
                            detect_prey, process_detection_results, self.thread_timeout, self.concurrency
                        ),
                        MAIN_LOOP
                    )
                    logger.info("Scheduled new prey detection analysis task on main asyncio loop")

            try:
                skip_image = (self.previous_image is not None) and (ssim(self.previous_image, image_array, data_range=image_array.max() - image_array.min(), channel_axis = 2) > self.ssim_threshold)
                if skip_image:
                    logger.info("Skipping image based on ssim")
                    return
                self.previous_image = image_array

                if prey_detector_tracker_config.image_size:
                    height, width = image_array.shape[:2]
                    crop_width = prey_detector_tracker_config.image_size[0]
                    
                    cropped_frame = crop_image(image_array, trigger_object_position, crop_width)
                    logger.debug(f"Image cropped from {width}x{height} to {cropped_frame.shape[1]}x{cropped_frame.shape[0]} (position: {trigger_object_position})")
                    
                    if prey_detector_tracker_config.image_size[1] < height:
                        raise NotImplementedError(f"Image height {height} is greater than the target height {prey_detector_tracker_config.image_size[1]}")
                else:
                    cropped_frame = image_array
                _, buffer = cv2.imencode('.jpg', cropped_frame)
                image_bytes = buffer.tobytes()
                async_consumer_queue.sync_q.put(image_bytes)
                logger.info(f"Image added to prey detection analysis queue {len(image_bytes)=}")
                
                if self.save_images:
                    self._save_detector_image(cropped_frame, datetime.now())
            except Exception as e:
                logger.error(f"Failed to process and queue image for prey detection analysis: {e}")
    
    def _save_detector_image(self, image_array: np.ndarray, timestamp: datetime) -> None:
        """Save the image sent to prey detector for analysis."""
        directory = f"{runtime_config.prey_detector_images_dir}/{self.uuid}"
        os.makedirs(directory, exist_ok=True)
        
        image_id = self._next_id
        self._next_id += 1
        
        filename = f"{directory}/{timestamp.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]}_id{image_id}.jpg"
        _, buffer = cv2.imencode('.jpg', image_array)
        with open(filename, 'wb') as f:
            f.write(buffer.tobytes())
        logger.debug(f"Saved prey detector analysis image: {filename=}")


class PausablePreyDetectorTracker(PreyDetectorTracker):
    """Tracks object detections over time to spawn prey detection analysis tasks and pauses during lock"""
    def __init__(self, prey_detection_enabled: bool = True, pause_during_lock: bool = True) :
        self.pause_during_lock = pause_during_lock
        super().__init__(prey_detection_enabled)

    def update(self, trigger_object_position: Literal["left", "middle", "right"] | None, image_array: np.ndarray) -> None:
        # Skip all prey detection analysis during lock
        if self.pause_during_lock and detection_pauser.should_pause_detection():
            if trigger_object_position:
                pause_reason = detection_pauser.get_pause_reason()
                logger.info(f"🔒 Prey detection tracker paused: {pause_reason=}")
            return  
        return super().update(trigger_object_position, image_array)