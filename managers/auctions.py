import asyncio
from typing import Dict, List

import inject
from fastapi import WebSocket

from app.utils.managers.redis_pubsub import RedisPubSubManager


class ConnectionManager:
    """
    Manages WebSocket connections and facilitates real-time communication
    for specific auction rooms using Redis Pub/Sub.
    """

    @inject.autoparams("pubsub_client")
    def __init__(self, pubsub_client: RedisPubSubManager):
        """
        Initializes the connection manager.
        """
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.pubsub_client = pubsub_client

    async def connect(self, websocket: WebSocket, auction_id: str):
        """
        Accepts a WebSocket connection and adds it to the active connections for the specified auction.
        """
        await websocket.accept()
        connections = self.active_connections
        if connections.get(auction_id):
            connections[auction_id].append(websocket)
        else:
            connections[auction_id] = [websocket]
            await self.pubsub_client.connect()
            pubsub_subscriber = await self.pubsub_client.subscribe(auction_id)
            asyncio.create_task(self._pubsub_data_reader(pubsub_subscriber))

    async def _pubsub_data_reader(self, pubsub_subscriber):
        """
        Listens to Redis Pub/Sub messages and forwards them to WebSocket connections.
        """
        while True:
            message = await pubsub_subscriber.get_message(
                ignore_subscribe_messages=True
            )
            if message is not None:
                auction_id = message["channel"].decode("utf-8")
                all_sockets = self.active_connections[auction_id]
                for socket in all_sockets:
                    data = message["data"].decode("utf-8")
                    await socket.send_text(data)

    async def broadcast(self, room_id: str, message: str) -> None:
        """
        Broadcasts a message to a Redis channel associated with a specific room.
        """
        await self.pubsub_client._publish(room_id, message)

    async def disconnect(self, websocket: WebSocket, auction_id: str):
        """
        Removes a WebSocket connection from the active connections for an auction.
        """
        self.active_connections[auction_id].remove(websocket)
        if len(self.active_connections[auction_id]) == 0:
            del self.active_connections[auction_id]
            await self.pubsub_client.unsubscribe(auction_id)
            print(f"{auction_id} disconnected")

    def has_active_connection(self, auction_id: str) -> bool:
        """
        Checks if there are active WebSocket connections for a specific auction.
        """
        return auction_id in self.active_connections and bool(
            self.active_connections[auction_id]
        )


connection_manager = ConnectionManager()
