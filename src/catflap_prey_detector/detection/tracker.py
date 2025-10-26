from __future__ import annotations
from datetime import datetime
import numpy as np
import os
import uuid
import random
import cv2
import logging
from ncnn.utils.objects import Detect_Object
from ncnn.utils.functional import iou_of
from ncnn.utils.visual import draw_detection_objects
from catflap_prey_detector.detection.config import tracker_config, runtime_config

logger = logging.getLogger(__name__)


# ssh deactivate for ncnn draw_detection_objects
cv2.imshow = lambda *args: None  # Do nothing
cv2.waitKey = lambda *args: None  # Do nothing

class DetectionTracker:
    """Tracks detections over time to avoid duplicate notifications for the same object."""
    
    def __init__(self, save_images: bool = False, class_names: list[str] | None = None) :
        """
        Initialize the detection tracker.
        """
        self.save_images = save_images
        self.tracked_objects: dict[str, TrackedObject] = {}
        self._next_id = 0
        self.class_names = class_names or []
        self.uuid = uuid.uuid4()
        
        logger.debug(f"Tracker {self.uuid=}")
    
    def _generate_object_key(self, detection: Detect_Object) -> str:
        """Generate a unique string key for an object that includes class name."""
        class_name = self.class_names[detection.label] if detection.label < len(self.class_names) else f"class_{detection.label}"
        obj_id = self._next_id
        self._next_id += 1
        return f"{class_name}_{obj_id}"
    
    def update(self, detections: list[Detect_Object], image_array: np.ndarray, timestamp: datetime) -> list[tuple[int, float, bytes]]:
        """
        Update tracker with new detections and return expired objects.
        
        Args:
            detections: List of new detections
            image_array: Current frame image as numpy array (BGR format)
            timestamp: Timestamp of the detections
            
        Returns:
            List of tuples (class_label, best_confidence, best_image_bytes) for each expired object
        """
        expired_objects = self._cleanup_old_objects(timestamp)
        
        if expired_objects:
            logger.info(f"Found {len(expired_objects)=} expired objects to process")
        
        image_with_detections = None
        if detections:
            logger.debug(f"Processing {len(detections)=} new detections")
            image_with_detections = self.draw_detections_on_image(image_array, detections, min_prob=0.0)
            
        for detection in detections:
            matched_key = self._find_matching_object(detection)
            
            if matched_key is not None:
                # Update existing tracked object
                self.tracked_objects[matched_key].update(detection, timestamp, image_with_detections)
                logger.debug(f"Updated existing object {matched_key=} with detection confidence {detection.prob:.3f}")
                
                if self.save_images:
                    self._save_image_for_object(matched_key, image_array, timestamp)

            else:
                # Create new tracked object
                new_key = self._generate_object_key(detection)
                tracked = TrackedObject(new_key, detection, timestamp, image_with_detections)
                self.tracked_objects[new_key] = tracked
                logger.info(f"Created new tracked object {new_key=} with confidence {detection.prob:.3f}")
                
                if self.save_images:
                    self._save_image_for_object(new_key, image_array, timestamp)
        
        # Return expired objects with their best image and confidence
        results = []
        for tracked in expired_objects:
            if tracked.best_image is not None:
                _, buffer = cv2.imencode('.jpg', tracked.best_image)
                image_bytes = buffer.tobytes()
                results.append((tracked.label, tracked.best_confidence, image_bytes))
        
        return results
    
    def _find_matching_object(self, detection: Detect_Object) -> str | None:
        """Find a tracked object that matches the given detection."""
        for obj_key, tracked in self.tracked_objects.items():
            if tracked.label == detection.label and self._calculate_iou(tracked.last_detection, detection) >= tracker_config.detection_iou_threshold:
                return obj_key
        return None
    
    def _calculate_iou(self, det1: Detect_Object, det2: Detect_Object) -> float:
        """Calculate Intersection over Union between two detections."""
        # Convert detections to [x1, y1, x2, y2] format for iou_of function
        box1 = np.array([
            det1.rect.x, 
            det1.rect.y, 
            det1.rect.x + det1.rect.w, 
            det1.rect.y + det1.rect.h
        ])
        box2 = np.array([
            det2.rect.x, 
            det2.rect.y, 
            det2.rect.x + det2.rect.w, 
            det2.rect.y + det2.rect.h
        ])
        
        # iou_of expects shape (N, 4), so reshape
        box1 = box1.reshape(1, 4)
        box2 = box2.reshape(1, 4)
        
        iou = iou_of(box1, box2)
        return float(iou[0])
    
    def _cleanup_old_objects(self, current_time: datetime) -> list[TrackedObject]:
        """Remove tracked objects that haven't been seen recently and return them."""
        expired_objects = []
        expired_keys = []
        
        for obj_key, tracked in self.tracked_objects.items():
            if (current_time - tracked.last_seen).total_seconds() > tracker_config.detection_time_window:
                expired_keys.append(obj_key)
                expired_objects.append(tracked)
        
        for obj_key in expired_keys:
            del self.tracked_objects[obj_key]
        
        return expired_objects
    
    def draw_detections_on_image(self, image: np.ndarray, detections: list[Detect_Object], min_prob: float = 0.0) -> np.ndarray:
        """
        Draw detection objects on the provided image.
        
        Args:
            image: Input image as numpy array (BGR format)
            detections: List of detection objects to draw
            min_prob: Minimum probability threshold for drawing detections
            
        Returns:
            Image with detections drawn on it
        """
        image_with_detections = image.copy()
        draw_detection_objects(image_with_detections, self.class_names, detections, min_prob=min_prob)
        return image_with_detections


    def _save_image_for_object(self, obj_key: str, image_array: np.ndarray, timestamp: datetime):
        """Save the image for the tracked object."""
        if random.random() > tracker_config.save_frequency:
            return
        try:
            directory = f"{runtime_config.detection_images_dir}/{self.uuid}_{obj_key}"
            os.makedirs(directory, exist_ok=True)
            filename = f"{directory}/{timestamp.strftime('%Y-%m-%d_%H-%M-%S-%f')[:-3]}.jpg"
            _, buffer = cv2.imencode('.jpg', image_array)
            with open(filename, 'wb') as f:
                f.write(buffer.tobytes())
            logger.debug(f"Saved image for object {obj_key=}: {filename=}")
        except Exception as e:
            logger.error(f"Failed to save image for object {obj_key=}: {e}")


class TrackedObject:
    """Represents a tracked object with detection history."""
    
    def __init__(self, obj_key: str, detection: Detect_Object, timestamp: datetime, image_array: np.ndarray):
        self.key = obj_key
        self.label = detection.label
        self.first_seen = timestamp
        self.last_seen = timestamp
        self.best_confidence = detection.prob
        self.best_image = image_array
        self.last_detection = detection
        self.detection_count = 1
    
    def update(self, detection: Detect_Object, timestamp: datetime, image_array: np.ndarray):
        """Update the tracked object with a new detection and optionally its image."""
        self.last_seen = timestamp
        self.last_detection = detection
        self.detection_count += 1
        
        if detection.prob >= self.best_confidence:
            self.best_confidence = detection.prob
            self.best_image = image_array
