import logging
import logging.handlers
import sys
import os
from catflap_prey_detector.detection.config import runtime_config


# Third-party libraries that log very noisily at INFO. httpx in particular logs
# a line on every Telegram getUpdates poll (~6x/minute, forever), which can grow
# the log to hundreds of MB and constantly write to the (flash) rootfs. Keeping
# them at WARNING also hides the bot token that httpx printed in every request URL.
_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "telegram",
    "telegram.ext",
    "apscheduler",
    "urllib3",
    "google",
    "googleapiclient",
    "PIL",
)


def setup_logging() -> logging.Logger:
    """Configure logging for the entire application"""
    # Create logs directory if it doesn't exist
    os.makedirs(runtime_config.log_dir, exist_ok=True)

    # Create a custom formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Rotating file handler so the log can never grow without bound and wear out
    # or fill the storage. 5 MB x 3 backups = 20 MB max.
    file_handler = logging.handlers.RotatingFileHandler(
        runtime_config.log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler for INFO and above (captured by journald under systemd)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Quiet the noisy third-party loggers.
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)

    return root_logger
