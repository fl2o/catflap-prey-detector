import os
import logging
import base64
import time
from datetime import datetime

import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_none
from catflap_prey_detector.hardware.catflap_controller import handle_prey_detection
from catflap_prey_detector.detection.detection_result import DetectionResult
from catflap_prey_detector.detection.config import runtime_config, prey_detection_api_config

logger = logging.getLogger(__name__)

request_counter = 0


@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(aiohttp.ClientError),
    wait=wait_none(),
    reraise=True
)
async def make_request(image_base64: str) -> bool:
    start_time = time.perf_counter()
    logger.info("Making request to Prey Detection API")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            prey_detection_api_config.api_url,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {prey_detection_api_config.prey_detector_api_key}',
            },
            json={
                'image_base64': image_base64,
            }
        ) as response:
            response.raise_for_status()
            data = await response.json()
            end_time = time.perf_counter()
            logger.info(f"Prey Detection API response received in {end_time - start_time:.2f}s")
            global request_counter
            request_counter += 1
            logger.info(f"Request counter: {request_counter}")
            
            prey_detected = data.get('detected', False)
            logger.info(f"API response: detected={prey_detected}")
            return prey_detected

async def detect_prey(image_bytes: bytes | None) -> DetectionResult:
    """
    Analyze image bytes for cat with prey detection.
    
    Args:
        image_bytes: Raw image data in bytes format (from cv2.imencode)
        
    Returns:
        DetectionResult object with detection status, message, and image data
    """
    try:
        if image_bytes is None:
            return DetectionResult.negative()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        prey_detected = await make_request(image_base64)
        if prey_detected:
            message = "🔒 CAT WITH PREY DETECTED! 🔒"
            lock_status_message = await handle_prey_detection()
            enhanced_message = f"{message}\n{lock_status_message}"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            os.makedirs(runtime_config.prey_images_dir, exist_ok=True)
            image_path = f"{runtime_config.prey_images_dir}/prey_{timestamp}.jpg"
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            logger.info(f"Persisted prey image at {image_path}")
            return DetectionResult.positive(enhanced_message, image_bytes)
        else:
            return DetectionResult.negative()
    except Exception as e:
        logger.error(f"Error processing image: {type(e).__name__}: {e}", exc_info=True)
        return DetectionResult.error(f"Error processing image: {type(e).__name__}: {e}", image_bytes)


async def main(image_base64: str) -> None:
    start_time = time.perf_counter()
    prey_detected = await make_request(image_base64)
    end_time = time.perf_counter()
    print(f"Response time: {(end_time - start_time) * 1000:.2f} ms")
    print(f"Prey detected: {prey_detected}")

if __name__ == "__main__":
    from catflap_prey_detector.classification.prey_detector_api.common import load_and_prepare_image, PREY_IMAGE_PATH
    
    # Use test image from tests directory
    image_path = PREY_IMAGE_PATH

    img, image_base64 = load_and_prepare_image(image_path, resize=False, target_size=384, show_image=True)
    asyncio.run(main(image_base64))

