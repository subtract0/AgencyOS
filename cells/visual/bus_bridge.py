
import asyncio
import json
import logging
from typing import Dict, Any, Callable
from cells.shared.message_bus import MessageBus

logger = logging.getLogger("BusBridge")

class BusBridge:
    """
    Bridges the persistent MessageBus to the ephemeral WebSocket clients.
    Subscribes to 'system', 'logs', 'hive' channels and broadcasts to WS.
    """
    
    def __init__(self, db_path: str = "messages.db", broadcast_func: Callable = None):
        self.db_path = db_path
        self.broadcast_func = broadcast_func # async function(msg_dict)
        self.running = False
        
    async def run(self):
        """Main bridge loop."""
        self.running = True
        logger.info("BusBridge started.")
        
        # We use the MessageBus context manager or manual init?
        # Manual is better for long-running service loop.
        bus = MessageBus(self.db_path)
        
        try:
            # Subscribe to relevant channels
            # We need a way to subscribe to MULTIPLE queues concurrently.
            # MessageBus.subscribe is an async generator.
            
            # We create tasks for each subscription
            await asyncio.gather(
                self._relay_channel(bus, "logs"),
                self._relay_channel(bus, "system"),
                self._relay_channel(bus, "hive"),
                self._relay_channel(bus, "voice")
            )
            
        except Exception as e:
            logger.error(f"BusBridge Error: {e}")
        finally:
            bus.close()
            
    async def _relay_channel(self, bus: MessageBus, channel: str):
        """Relays a single channel to the websocket broadcast."""
        logger.info(f"Relaying channel: {channel}")
        async for msg in bus.subscribe(channel):
            if not self.running:
                break
                
            # Process message
            try:
                # We expect msg['message_data'] to be a dict
                data = msg['message_data']
                
                # We need to format it for the frontend.
                # The frontend expects: { "type": "update", "data": SYSTEM_STATE }
                # OR we teach frontend to handle Streamed Events.
                # For now, let's inject into SYSTEM_STATE-like updates if possible, 
                # or send a special "event" type.
                
                # Let's send a raw event and let dashboard.py handle state updates?
                # Or trigger a state update?
                
                # APPROACH: We broadcast a "bus_event" type.
                payload = {
                    "type": "bus_event",
                    "channel": channel,
                    "data": data
                }
                
                if self.broadcast_func:
                    await self.broadcast_func(payload)
                
                # Ack the message so we don't re-send next restart (unless we want replay?)
                # For logs/events, reliable delivery is good. 
                await bus.ack(msg['_message_id'])
                
            except Exception as e:
                logger.error(f"Error bridging message: {e}")

