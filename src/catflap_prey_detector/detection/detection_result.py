"""
Detection result dataclass for standardizing prey detection outputs.
"""
from dataclasses import dataclass


@dataclass
class DetectionResult:
    """
    Standardized result from prey detection analysis.
    
    This dataclass eliminates hidden dependencies by providing a clear contract
    for detection results across the system.
    """
    is_positive: bool
    message: str | None = None
    image_bytes: bytes | None = None
    
    @classmethod
    def positive(cls, message: str, image_bytes: bytes) -> 'DetectionResult':
        """Create a positive detection result."""
        return cls(is_positive=True, message=message, image_bytes=image_bytes)
    
    @classmethod
    def negative(cls) -> 'DetectionResult':
        """Create a negative detection result."""
        return cls(is_positive=False)
    
    @classmethod
    def error(cls, error_message: str, image_bytes: bytes | None = None) -> 'DetectionResult':
        """Create an error detection result (treated as negative but with message)."""
        return cls(is_positive=False, message=error_message, image_bytes=image_bytes)
    
    def __bool__(self) -> bool:
        """Allow boolean evaluation - True for positive detections, False otherwise."""
        return self.is_positive
    
