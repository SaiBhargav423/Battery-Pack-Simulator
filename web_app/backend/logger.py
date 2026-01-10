"""
Runtime Error Logger

Catches and logs all runtime errors with complete trace information to a text file.
"""

import logging
import sys
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional

# Create logs directory if it doesn't exist
backend_dir = Path(__file__).parent.resolve()
logs_dir = backend_dir / 'logs'
logs_dir.mkdir(exist_ok=True)

# Log file path
log_file = logs_dir / 'runtime_errors.log'

# Configure root logger
logger = logging.getLogger('bms_simulator')
logger.setLevel(logging.ERROR)  # Only log errors and above

# Remove existing handlers to avoid duplicates
logger.handlers.clear()

# File handler for error logging
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.ERROR)

# Formatter with timestamp and full traceback
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# Console handler for immediate feedback
console_handler = logging.StreamHandler(sys.stderr)
console_handler.setLevel(logging.ERROR)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def log_exception(exc_type, exc_value, exc_traceback, context: Optional[str] = None):
    """
    Log an exception with full traceback.
    
    Args:
        exc_type: Exception type
        exc_value: Exception value
        exc_traceback: Exception traceback
        context: Optional context string (e.g., "API endpoint", "Simulation loop")
    """
    if exc_type is None:
        return
    
    # Format full traceback
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    full_traceback = ''.join(tb_lines)
    
    # Build error message
    error_msg = f"Exception occurred"
    if context:
        error_msg += f" in {context}"
    error_msg += f": {exc_type.__name__}: {exc_value}\n\nFull Traceback:\n{full_traceback}"
    
    logger.error(error_msg)


def log_error(message: str, exc_info: Optional[Exception] = None, context: Optional[str] = None):
    """
    Log an error message with optional exception info.
    
    Args:
        message: Error message
        exc_info: Optional exception object
        context: Optional context string
    """
    error_msg = message
    if context:
        error_msg = f"[{context}] {message}"
    
    if exc_info:
        logger.error(error_msg, exc_info=exc_info)
    else:
        logger.error(error_msg)


def setup_exception_hook():
    """
    Set up global exception hook to catch all unhandled exceptions.
    """
    def exception_hook(exc_type, exc_value, exc_traceback):
        # Don't log KeyboardInterrupt (Ctrl+C)
        if exc_type == KeyboardInterrupt:
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        log_exception(exc_type, exc_value, exc_traceback, context="Unhandled Exception")
        # Also call default handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = exception_hook


def get_log_file_path() -> Path:
    """Get the path to the log file."""
    return log_file


def clear_log():
    """Clear the log file (use with caution)."""
    if log_file.exists():
        log_file.write_text('')


def get_recent_errors(limit: int = 50) -> list:
    """
    Get recent error entries from the log file.
    
    Args:
        limit: Maximum number of lines to return
        
    Returns:
        List of error log lines
    """
    if not log_file.exists():
        return []
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-limit:] if len(lines) > limit else lines
    except Exception as e:
        return [f"Error reading log file: {e}"]


# Initialize exception hook on import
setup_exception_hook()

print(f"[LOGGER] Runtime error logger initialized")
print(f"[LOGGER] Log file: {log_file}")
print(f"[LOGGER] Logging all runtime errors with full tracebacks")
