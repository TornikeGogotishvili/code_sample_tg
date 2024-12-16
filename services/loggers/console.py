import logging

from app.services.loggers.base import BaseLogger


class ConsoleLogger(BaseLogger):

    def __init__(self):
        super().__init__(logger_name="auction-logs")

    def _send_log(self, message: str, severity: str) -> None:
        if severity == "ERROR":
            logging.error(message)
        elif severity == "WARNING":
            logging.warning(message)
        elif severity == "DEBUG":
            logging.debug(message)
        elif severity == "CRITICAL":
            logging.critical(message)
        else:
            logging.info(message)

        print(message)