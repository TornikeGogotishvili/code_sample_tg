from typing import Dict, Optional

import inject

from app.services.loggers.base import BaseLogger


class AuditLogger:
    """Handles logging of user, auction, and bidding actions."""

    @inject.autoparams()
    def __init__(self, logger: BaseLogger):
        """Use dependency injection to get the logger (Cloud or Console)"""
        self.logger = logger

    def log(
        self,
        action: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, any]] = None,
        severity: str = "INFO",
        trace_id: Optional[str] = None
    ) -> None:
        self.logger.log(action, user_id, metadata, severity, trace_id)

    def warn(self, message: str, trace_id: Optional[str] = None) -> None:
        self.logger.warn(message, trace_id)

    def error(self, message: str, trace_id: Optional[str] = None) -> None:
        self.logger.error(message, trace_id)

    def debug(self, message: str, trace_id: Optional[str] = None) -> None:
        self.logger.debug(message, trace_id)

    def critical(self, message: str, trace_id: Optional[str] = None) -> None:
        self.logger.critical(message, trace_id)
