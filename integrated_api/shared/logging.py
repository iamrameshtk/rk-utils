# shared/logging.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_level=logging.INFO):
    """Configure and return a logger with the given name"""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configure logging
    logger = logging.getLogger(name)
    
    # Set log level
    logger.setLevel(log_level)
    
    # Only add handlers if they don't already exist
    if not logger.handlers:
        # Create formatters
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_formatter = logging.Formatter(
            "%(levelname)s - %(message)s"
        )
        
        # Create handlers
        # File handler with rotation (10 MB per file, max 5 files)
        file_handler = RotatingFileHandler(
            f"logs/{name}.log", 
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger