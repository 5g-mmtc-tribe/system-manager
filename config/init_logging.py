import os
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_file_path, log_level=logging.INFO, log_format=None):
    """
    Initializes and configures the root logger.
    """
    # If no format is provided, use a default
    if log_format is None:
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

    # Create the log directory if it doesn’t exist
    log_dir = os.path.dirname(log_file_path)
    os.makedirs(log_dir, exist_ok=True)

    # Configure handlers
    # For example, use TimedRotatingFileHandler to rotate logs daily.
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when="midnight",   # rotate at midnight
        backupCount=7      # keep 7 old log files
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # You might also want a console handler in development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Get the root logger and set the level
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates if re-run
    logger.handlers.clear()

    # Add new handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.info("Logging is configured and file is in the logs folder.")

    return logger
