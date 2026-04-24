# app/utils/logger.py
# FULL FINAL LOGGER FILE

import os
import sys
from loguru import logger

# =====================================================
# CREATE LOG FOLDER
# =====================================================
os.makedirs("logs", exist_ok=True)

# remove default logger
logger.remove()

# =====================================================
# CONSOLE LOG
# =====================================================
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    backtrace=False,
    diagnose=False,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:"
        "<cyan>{function}</cyan>:"
        "<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
)

# =====================================================
# FILE LOG
# =====================================================
logger.add(
    "logs/app.log",
    level="INFO",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    enqueue=True,
    encoding="utf-8",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
)

# =====================================================
# READY MESSAGE
# =====================================================
logger.info("Logger Initialized")