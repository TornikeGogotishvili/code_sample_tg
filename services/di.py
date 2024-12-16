import os

import google.cloud.logging
import inject

from app.services.loggers import AuditLogger
from app.services.loggers.base import BaseLogger
from app.services.loggers.cloud_logger import CloudLogger
from app.services.loggers.console import ConsoleLogger
from app.utils.managers.redis_pubsub import RedisPubSubManager


def configure_injection(binder: inject.Binder):
    """Configure dependencies for dependency injection"""
    environment = os.getenv("ENVIRONMENT", "dev")
    if environment == "prod":
        binder.bind_to_provider(BaseLogger, CloudLogger)
        binder.bind(google.cloud.logging.Client, google.cloud.logging.Client())
    else:
        binder.bind_to_provider(BaseLogger, ConsoleLogger)

    binder.bind_to_provider(AuditLogger, AuditLogger())
    binder.bind_to_provider(RedisPubSubManager, RedisPubSubManager())
