"""YOLO detector wrapper for NCNN models."""
import logging
import numpy as np
import ncnn
from ncnn.utils.functional import nms, xywh2xyxy
from ncnn.utils.objects import Detect_Object

from catflap_prey_detector.detection.config import YOLOConfig, yolo_config

logger = logging.getLogger(__name__)



class YOLODetector:
    """Wrapper for YOLO NCNN model."""
    COCO_CLASS_NAMES: list[str] = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
            "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
            "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
            "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
            "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
            "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
            "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
            "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
            "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
        ]
    config: YOLOConfig = yolo_config
    classes_of_interest = config.classes_of_interest
    
    @classmethod
    def get_class_id(cls, class_name: str) -> int:
        """Get the indices of classes of interest."""
        try:
            return cls.classes_of_interest.index(class_name)
        except ValueError:
            raise ValueError(f"Class {class_name} not found in {cls.classes_of_interest=}")
    
    def __init__(self):
        """Initialize the YOLO detector.
        """
        self.classes_of_interest_ids = [self.COCO_CLASS_NAMES.index(name) for name in self.classes_of_interest]
        self.load_model()
        
    def load_model(self) -> None:
        """Load the NCNN model.
        
        Args:
            param_path: Path to the .param file
            bin_path: Path to the .bin file
        """
        try:
            logger.info(f"Loading YOLO model from {self.config.model_param_path}")
            self.net = ncnn.Net()
            self.net.load_param(self.config.model_param_path)
            self.net.load_model(self.config.model_bin_path)
            logger.info("YOLO model loaded successfully")
            logger.info(f"Detection parameters: class_thresholds={self.config.class_thresholds}, "
                       f"iou_threshold={self.config.iou_threshold}")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}", exc_info=True)
            raise
            
    def detect(self, image: np.ndarray) -> list[Detect_Object]:
        """Run detection on an image.
        
        Args:
            image: Input image as numpy array (RGB format)
            
        Returns:
            List of detected objects
        """
        try:
            # Prepare input
            mat_in = ncnn.Mat.from_pixels_resize(
                image, 
                ncnn.Mat.PixelType.PIXEL_RGB, 
                image.shape[1],  # width
                image.shape[0],  # height
                self.config.image_size[1],
                self.config.image_size[0]
            )
            mat_in.substract_mean_normalize([0, 0, 0], [1/255.0, 1/255.0, 1/255.0])
            
            # Run inference
            with self.net.create_extractor() as ex:
                ex.input("in0", mat_in)
                _, mat_out = ex.extract("out0")
                
            # Process predictions
            pred = np.array(mat_out).T
            
            # Split predictions
            boxes = pred[:, :4]  # x, y, w, h
            class_scores = pred[:, 4:]  # All class scores
            
            # Filter by classes of interest
            class_scores = class_scores[:, self.classes_of_interest_ids]
            
            thresholds = np.array([self.config.class_thresholds[class_name] for class_name in self.classes_of_interest])
            
            confidences = class_scores.max(axis=1)
            class_indices = class_scores.argmax(axis=1)
            mask = confidences > thresholds[class_indices]
            
            if not mask.any():
                return []
            
            # Filter by minimum detection area
            areas = boxes[:, 2] * boxes[:, 3]
            area_mask = areas > self.config.min_detection_area
            mask = mask & area_mask
            if not mask.any():
                logger.info(f"All detections filtered out by minimum area threshold: {areas.max()}")
                return []

            boxes = boxes[mask]
            class_scores = class_scores[mask]
            confidences = confidences[mask]
            
            # Apply NMS
            boxes_xyxy = xywh2xyxy(boxes)
            picked_indices = nms(boxes_xyxy, confidences, self.config.iou_threshold)
            
            # Create detection objects
            detections = []
            for idx in picked_indices:
                class_idx = np.argmax(class_scores[idx])
                
                detections.append(
                    Detect_Object(
                        label=class_idx,
                        prob=confidences[idx],
                        x=boxes_xyxy[idx][0],
                        y=boxes_xyxy[idx][1],
                        w=boxes_xyxy[idx][2] - boxes_xyxy[idx][0],
                        h=boxes_xyxy[idx][3] - boxes_xyxy[idx][1]
                    )
                )
                
            return detections
            
        except Exception as e:
            logger.error(f"Error during YOLO inference: {e}", exc_info=True)
            return []

if __name__ == "__main__":
    import cv2
    import time
    from catflap_prey_detector.classification.prey_detector_api.common import PREY_IMAGE_PATH
    
    yolo_detector = YOLODetector()
    # Use test image from tests directory
    image = cv2.imread(PREY_IMAGE_PATH)
    print("image shape", image.shape)
    start_time = time.time()
    detections = yolo_detector.detect(image)
    detection_time = time.time() - start_time
    
    print(f"Detection took {detection_time:.3f}s")
    for detection in detections:
        class_name = yolo_detector.classes_of_interest[detection.label]
        print(f"Detected {class_name=} with confidence {detection.prob:.3f}")