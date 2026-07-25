import asyncio
import json
import logging
from typing import Set, Dict, Any

logger = logging.getLogger(__name__)

class EventBroadcaster:
    """
    In-memory PubSub manager for Server-Sent Events (SSE).
    Allows client connections (Admin Dashboards) to subscribe and receive real-time updates.
    """
    def __init__(self):
        self.subscribers: Set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.subscribers.add(queue)
        logger.info(f"New SSE client connected. Total active clients: {len(self.subscribers)}")
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        self.subscribers.discard(queue)
        logger.info(f"SSE client disconnected. Remaining active clients: {len(self.subscribers)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        if not self.subscribers:
            return

        payload = json.dumps({"event": event_type, "data": data})
        message = f"event: {event_type}\ndata: {payload}\n\n"

        for queue in list(self.subscribers):
            try:
                queue.put_nowait(message)
            except Exception as e:
                logger.error(f"Error broadcasting to SSE subscriber: {e}")

broadcaster = EventBroadcaster()
