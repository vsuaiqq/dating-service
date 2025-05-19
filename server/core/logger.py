import os
import logging
from logging.handlers import TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger
from rich.logging import RichHandler

from core.config import get_settings

settings = get_settings()

LOG_DIR = "logs"
LOG_FILE = "app.log"
LOG_PATH = os.path.join(LOG_DIR, LOG_FILE)
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger():
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger = logging.getLogger("app")
    logger.setLevel(level)

    formatter = None
    if settings.LOG_FORMAT == "json":
        formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(correlation_id)s')
    else:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

    file_handler = TimedRotatingFileHandler(LOG_PATH, when="midnight", backupCount=7, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if settings.LOG_FORMAT == "json":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
    else:
        console_handler = RichHandler(rich_tracebacks=True, markup=True)
        console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.propagate = False

    return logger

logger = setup_logger()
