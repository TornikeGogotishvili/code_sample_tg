import json
import uuid
from typing import Callable

import aio_pika
import inject
import asyncio

from app.core.config import settings
from app.services.loggers import AuditLogger
from app.utils import validate_message_schema


class EventSubscriber:
    """
    A subscriber class for handling RabbitMQ messages.
    """

    @inject.autoparams("audit_logger")
    def __init__(
        self, exchange_name: str, dead_letter_exchange: str, audit_logger: AuditLogger
    ):
        """
        Initializes the instance with connection settings.
        """
        self.connection_url = settings.rabbitmq_url.unicode_string()
        self.exchange_name = exchange_name
        self.connection = None
        self.channel = None
        self.dead_letter_exchange = dead_letter_exchange
        self.retry_exchange = "retry_exchange"
        self.max_retries = 5
        self.message_ttl = 300000
        self.max_message_count = 1000
        self.logger = audit_logger

    async def connect(self):
        """
        Establishes a connection and sets up exchanges and queues.
        """
        try:
            self.connection = await aio_pika.connect_robust(self.connection_url)
            self.channel = await self.connection.channel()

            await self.channel.declare_exchange(self.exchange_name, type="fanout")
            await self.channel.declare_exchange(
                self.dead_letter_exchange, type="fanout"
            )
            await self.channel.declare_exchange(self.retry_exchange, type="direct")

            await self.__declare_dead_letter_queue()

        except aio_pika.AMQPConnectionError as e:
            self.logger.error(f"Error while connecting to RabbitMQ: {e}")
            raise

    async def __declare_dead_letter_queue(self):
        """
        Declare the dead letter queue for failed messages.
        """
        queue = await self.channel.declare_queue(
            "dead_letter_queue",
            durable=True,
            arguments={"x-message-ttl": self.message_ttl},
        )
        await queue.bind(exchange=self.dead_letter_exchange)

    async def subscribe_events(self, queue_name: str, callback: Callable):
        """
        Subscribes to events on a specified queue and processes them using a callback.
        """
        try:
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                auto_delete=False,
                arguments={
                    "x-message-ttl": self.message_ttl,
                    "x-dead-letter-exchange": self.dead_letter_exchange,
                    "x-max-length": self.max_message_count,
                },
            )
            await queue.bind(exchange=self.exchange_name)
            await queue.consume(self._consume_message(callback), no_ack=False)

        except aio_pika.AMQPError as e:
            self.logger.error(f"Error while subscribing to queue {queue_name}: {e}")
            raise

    async def _consume_message(self, callback):
        async def on_message(message: aio_pika.IncomingMessage):
            async with message.process():
                try:
                    request_id = message.headers.get("request_id") if message.headers else str(
                        uuid.uuid4())
                    self.logger.log(f"Processing message with Request ID: {request_id}")

                    message_data = await self._deserialize_and_validate_message(message)
                    await callback(message_data, request_id)
                except ValueError as e:
                    self.logger.error(f"Deserialization/Validation failed (Request ID: {request_id}): {e}")
                    await self._handle_failed_message(message, request_id)
                except Exception as e:
                    self.logger.error(f"Unexpected error (Request ID: {request_id}): {e}")
                    await self._handle_failed_message(message, request_id)

        return on_message

    async def _deserialize_and_validate_message(self, message: aio_pika.IncomingMessage):
        try:
            message_data = json.loads(message.body)
            validate_message_schema(message_data)
            return message_data
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid message format: {e}")

    async def _handle_failed_message(self, message: aio_pika.IncomingMessage, request_id):
        retries = (message.headers or {}).get("x-retries", 0)
        if retries < self.max_retries:
            retries += 1
            await asyncio.sleep(2 ** retries)
            self.logger.warning(f"Retry {retries}/{self.max_retries} for message (Request ID: {request_id})")

            await self.channel.exchange(self.retry_exchange).publish(
                aio_pika.Message(
                    body=message.body,
                    headers={
                        "x-retries": retries,
                        "request_id": request_id
                    }
                ),
                routing_key="retry_queue"
            )
        else:
            self.logger.warn(
                f"Message moved to dead-letter queue after {retries} retries (Request ID: {request_id})")
            await self.channel.exchange(self.dead_letter_exchange).publish(
                aio_pika.Message(
                    body=message.body,
                    headers={
                        "request_id": request_id
                    }
                )
            )
    async def close(self):
        """
        Closes the channel and connection.
        """
        try:
            await self.channel.close()
            await self.connection.close()
            self.logger.log("Connection to RabbitMQ closed.")
        except Exception as e:
            self.logger.error(f"Error closing RabbitMQ connection: {e}")
            raise


def create_handler(name):
    async def on_event_received(message: aio_pika.IncomingMessage):
        async with message.process(ignore_processed=True):
            message_body = message.body.decode("utf-8")
            try:
                # Each message headers contain event_type, which can
                # be used to assign handlers to different messages
                pass

            except Exception as e:
                print("There was an error", e)
                await message.reject(requeue=False)

    return on_event_received