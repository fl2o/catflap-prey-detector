import asyncio
import threading
import signal
import sys
import logging
import os
import time

from catflap_prey_detector.notifications.telegram_bot import main as bot_main
from catflap_prey_detector.detection.detection_pipeline import run_detection_pipeline
from catflap_prey_detector.core.logging import setup_logging
from catflap_prey_detector.cloud.sync_scheduler import run_cloud_sync_loop
from catflap_prey_detector.detection.config import detector_config

# Global reference to the main asyncio event loop
MAIN_LOOP: asyncio.AbstractEventLoop | None = None


def signal_handler(signum, frame):
    """Handle shutdown gracefully"""
    logger = logging.getLogger(__name__)
    logger.info("Shutdown signal received, terminating application...")
    sys.exit(0)


def _supervise_detection(*args) -> None:
    """Run the detection pipeline forever, restarting it if it ever stops.

    The pipeline is meant to loop indefinitely; if it returns or raises (e.g. a
    camera fault), restart it with capped exponential backoff so detection can
    never silently stay dead while the rest of the process keeps running.
    """
    logger = logging.getLogger(__name__)
    backoff = 5
    while True:
        started = time.monotonic()
        try:
            run_detection_pipeline(*args)
            logger.error("Detection pipeline exited unexpectedly; restarting in %ss", backoff)
        except Exception:
            logger.exception("Detection pipeline crashed; restarting in %ss", backoff)
        # If it had been running healthily for a while, reset the backoff.
        if time.monotonic() - started > 300:
            backoff = 5
        time.sleep(backoff)
        backoff = min(backoff * 2, 60)


async def app():
    global MAIN_LOOP
    MAIN_LOOP = asyncio.get_running_loop()
    setup_logging()
    main_logger = logging.getLogger(__name__)
    
    main_logger.info("=== Starting Catflap Prey Detector Application ===")
    main_logger.info(f"Process ID: {os.getpid()=}")
    main_logger.info(f"Python version: {sys.version}")
    
    # Set up signal handler for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    main_logger.info("Signal handlers configured for graceful shutdown")
    
    try:
        main_logger.info("Initializing camera detector thread...")
        detector_thread = threading.Thread(
            target=_supervise_detection,
            args=(
                detector_config.telegram_enabled, 
                detector_config.save_images, 
                detector_config.prey_detection_enabled
            ), 
            daemon=True
        )
        detector_thread.start()
        main_logger.info("Object detector started in background thread")
        
        if detector_config.cloud_sync_enabled:
            asyncio.create_task(run_cloud_sync_loop())
            main_logger.info("Cloud sync started successfully")
        else:
            main_logger.info("Cloud sync is disabled")
        
        if detector_config.telegram_enabled:
            main_logger.info("Starting Telegram bot...")
            await bot_main()
        else:
            main_logger.info("Telegram bot is disabled")
            while True:
                await asyncio.sleep(1000)
        
    except Exception as e:
        main_logger.error(f"Critical error in main application: {e}", exc_info=True)
        raise


def main():
    """Entry point for the CLI command"""
    asyncio.run(app())


if __name__ == "__main__":
    main()
