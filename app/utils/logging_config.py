"""
Structured Logging Configuration

Provides JSON-formatted logging with automatic log rotation.
Configurable via environment variables:
- LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- LOG_FORMAT: Output format (json or text)
- LOG_FILE: Path to log file
- LOG_MAX_BYTES: Max log file size before rotation (default: 10MB)
- LOG_BACKUP_COUNT: Number of backup files to keep (default: 5)
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from logging.handlers import RotatingFileHandler
import os


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.

    Outputs logs in JSON format with consistent fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (DEBUG, INFO, etc.)
    - logger: Logger name
    - message: Log message
    - Additional fields from extra parameter
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add standard fields that might be useful
        log_data["module"] = record.module
        log_data["function"] = record.funcName
        log_data["line"] = record.lineno

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Format: timestamp - name - level - message
    """

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Setup application logging with structured JSON or text output.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format (json or text)
        log_file: Optional path to log file. If not provided, logs to stdout only
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
    """
    # Get log level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Choose formatter
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Log startup message
    root_logger.info(
        f"Logging configured: level={log_level}, format={log_format}, file={log_file}"
    )


def get_logging_config_from_env() -> Dict[str, Any]:
    """
    Get logging configuration from environment variables.

    Returns:
        Dictionary with logging configuration
    """
    return {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "log_format": os.getenv("LOG_FORMAT", "text"),
        "log_file": os.getenv("LOG_FILE"),
        "max_bytes": int(os.getenv("LOG_MAX_BYTES", str(10 * 1024 * 1024))),
        "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
    }


def configure_logging_from_env() -> None:
    """
    Configure logging from environment variables.

    This is a convenience function that reads configuration from
    environment variables and calls setup_logging().
    """
    config = get_logging_config_from_env()
    setup_logging(**config)
