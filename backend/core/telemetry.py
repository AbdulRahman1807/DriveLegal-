import structlog
import asyncio
from datetime import datetime

logger = structlog.get_logger(__name__)

class TelemetryEngine:
    """
    A non-blocking telemetry engine.
    In a real system, this could write to a timeseries DB or Kafka.
    Here we simulate flushing metrics to a local file/logger.
    """
    def __init__(self):
        self.queue = None
        self.worker_task = None

    async def _worker(self):
        while True:
            try:
                event = await self.queue.get()
                # Simulate I/O bound insert
                await asyncio.sleep(0.01)
                logger.info(f"TELEMETRY_LOG: {event}")
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Telemetry worker error: {e}")

    async def log_event(self, event_type: str, metadata: dict):
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "metadata": metadata
        }
        
        if self.queue is None:
            self.queue = asyncio.Queue(maxsize=1000)
            self.worker_task = asyncio.create_task(self._worker())
            
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Telemetry queue full, dropping event.")

# Global instance
telemetry = TelemetryEngine()
