import redis.asyncio as aioredis

from app.core.config import settings


class RedisPubSubManager:
    def __init__(self):
        self.redis_location = settings.REDIS_LOCATION
        self.redis_connection = None
        self.pubsub = None

    async def _get_redis_connection(self) -> aioredis.Redis:
        """
        Establishes a connection to Redis.
        """
        return aioredis.Redis.from_url(self.redis_location)

    async def connect(self) -> None:
        """
        Connects to the Redis server and initializes the pubsub client.
        """
        self.redis_connection = await self._get_redis_connection()
        self.pubsub = self.redis_connection.pubsub()

    async def _publish(self, room_id: str, message: str) -> None:
        """
        Publishes a message to a specific Redis channel.
        """
        await self.redis_connection.publish(room_id, message)

    async def subscribe(self, room_id: str) -> aioredis.Redis:
        """
        Subscribes to a Redis channel.
        """
        await self.pubsub.subscribe(room_id)
        return self.pubsub

    async def unsubscribe(self, room_id: str) -> None:
        """
        Unsubscribes from a Redis channel.
        """
        await self.pubsub.unsubscribe(room_id)
