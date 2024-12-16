import logging

import google.cloud.logging
import inject

from app.services.loggers.base import BaseLogger


class CloudLogger(BaseLogger):
    """Send logs to Google Cloud Logging."""

    @inject.autoparams("client")
    def __init__(
        self, client: google.cloud.logging.Client, logger_name: str = "auction-logs"
    ):
        super().__init__(logger_name)
        self.client = client
        self.client.setup_logging()
        self.logger = self.client.logger(logger_name)

    def _send_log(self, message: str, severity: str) -> None:
        try:
            self.logger.log_text(message, severity=severity)
        except Exception as e:
            logging.error(f"Failed to send log to Cloud Logging: {e}")

