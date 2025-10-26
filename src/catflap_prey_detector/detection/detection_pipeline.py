import logging
from datetime import datetime

from catflap_prey_detector.notifications.telegram_bot import notify_event
from catflap_prey_detector.notifications import telegram_bot
from catflap_prey_detector.detection.tracker import DetectionTracker
from catflap_prey_detector.detection.prey_detector_tracker import PausablePreyDetectorTracker
from catflap_prey_detector.detection.config import detector_config
from catflap_prey_detector.detection.camera_manager import CameraManager
from catflap_prey_detector.detection.yolo_detector import YOLODetector

logger = logging.getLogger(__name__)

def run_detection_pipeline(notify_telegram=False, save_images=False, prey_detection_enabled=False):
    logger.info("=== Starting Camera Detection System ===")
    logger.info(f"Configuration: {notify_telegram=}, {save_images=}, {prey_detection_enabled=}")
    
    camera_manager = CameraManager()
    
    # Set the global camera manager for telegram bot access
    telegram_bot.camera_manager = camera_manager
    
    logger.info("Initializing YOLO detector...")
    yolo_detector = YOLODetector()
    
    logger.info("Initializing detection trackers...")
    detection_tracker = DetectionTracker(
        class_names=yolo_detector.classes_of_interest,
        save_images=save_images
    )
    logger.info("Initializing prey detector tracker...")
    prey_detector_tracker = PausablePreyDetectorTracker(
        prey_detection_enabled=detector_config.prey_detection_enabled,
        pause_during_lock=True
    )
    
    with camera_manager:
        logger.info("=== Starting main detection loop ===")
        try:
            while True:
                try:
                    current_frame = camera_manager.capture_frame()
                    timestamp = datetime.now()
                    logger.debug(f"Captured frame at {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                    
                except Exception as e:
                    logger.error(f"Error capturing frame: {e}", exc_info=True)
                    continue
                    
                try:
                    detections = yolo_detector.detect(current_frame)
                    
                    trigger_object_position = None
                    
                    if detections:
                        for detection in detections:
                            class_name = yolo_detector.classes_of_interest[detection.label]
                            logger.debug(f"Detected {class_name=} with confidence {detection.prob:.3f}")
                            
                            if detection.label == detector_config.prey_detection_trigger_class_id:
                                bbox_center_x = detection.rect.x + detection.rect.w / 2
                                frame_width = current_frame.shape[1]
                                
                                if bbox_center_x < frame_width / 3:
                                    trigger_object_position = "left"
                                elif bbox_center_x > 2 * frame_width / 3:
                                    trigger_object_position = "right"
                                else:
                                    trigger_object_position = "middle"
                        
                        logger.info(f"Found {len(detections)} objects at {timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}, {trigger_object_position=}")
                    else:
                        logger.debug("No objects detected")
                    
                except Exception as e:
                    logger.error(f"Error during YOLO inference: {e}", exc_info=True)
                    detections = []
                    trigger_object_position = None
                
                try:
                    expired_objects = detection_tracker.update(detections, current_frame, timestamp)
                    prey_detector_tracker.update(trigger_object_position, current_frame)
                    
                    if trigger_object_position and detector_config.detection_followup_frames > 0:
                        logger.info(f"Trigger object detected at {trigger_object_position}, collecting next {detector_config.detection_followup_frames} frames for prey detection analysis")
                        for i in range(detector_config.detection_followup_frames):
                            followup_frame = camera_manager.capture_frame()
                            followup_timestamp = datetime.now()
                            logger.debug(f"Captured followup frame {i+1}/{detector_config.detection_followup_frames} at {followup_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}")
                            prey_detector_tracker.update(trigger_object_position, followup_frame)
                    
                    for label, confidence, best_image_bytes in expired_objects:
                        class_name = yolo_detector.classes_of_interest[label]
                        logger.info(f"Expired detection: {class_name=} (confidence: {confidence:.3f})")
                        
                        if notify_telegram:
                            message = f"{class_name.capitalize()} detected at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                            try:
                                notify_event(message, best_image_bytes)
                                logger.info(f"Telegram notification sent for {class_name=} detection")
                            except Exception as e:
                                logger.error(f"Failed to send telegram notification: {e}")
                                
                except Exception as e:
                    logger.error(f"Error updating trackers or sending notifications: {e}", exc_info=True)
                    
        except KeyboardInterrupt:
            logger.info("Detection loop interrupted by user")
        except Exception as e:
            logger.error(f"Critical error in detection loop: {e}", exc_info=True)
            raise

if __name__ == "__main__":
    run_detection_pipeline(notify_telegram=False, save_images=False, prey_detection_enabled=False)