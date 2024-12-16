import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional

import google.cloud.logging
import inject


class BaseLogger(ABC):
    """Abstract base logger class for logs."""

    def __init__(self, logger_name: str):
        self.logger_name = logger_name

    @abstractmethod
    def _send_log(self, message: str, severity: str) -> None:
        """Abstract method to send log to a destination (e.g., Cloud or Console)"""
        pass

    def _log_text(self, message: str, severity: str, trace_id: Optional[str] = None) -> None:
        """Helper to log text with a given severity and optional trace ID"""
        formatted_message = f"{severity}: [{self.logger_name}] {message}"
        if trace_id:
            formatted_message += f" | trace_id={trace_id}"
        try:
            self._send_log(formatted_message, severity)
        except Exception as e:
            logging.error(f"Failed to send log: {e}")

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, any]] = None,
        severity: str = "INFO",
        trace_id: Optional[str] = None
    ) -> None:
        log_data = {"action": action}

        if user_id:
            log_data["user_id"] = user_id
        if metadata:
            log_data["metadata"] = metadata

        self._log_text(f"{log_data}", severity=severity, trace_id=trace_id)

    def warn(self, message: str, trace_id: Optional[str] = None) -> None:
        self._log_text(f"WARNING: {message}", severity="WARNING", trace_id=trace_id)

    def error(self, message: str, trace_id: Optional[str] = None) -> None:
        self._log_text(f"ERROR: {message}", severity="ERROR", trace_id=trace_id)

    def debug(self, message: str, trace_id: Optional[str] = None) -> None:
        self._log_text(f"DEBUG: {message}", severity="DEBUG", trace_id=trace_id)

    def critical(self, message: str, trace_id: Optional[str] = None) -> None:
        self._log_text(f"CRITICAL: {message}", severity="CRITICAL", trace_id=trace_id)

