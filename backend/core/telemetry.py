import structlog
import asyncio
from datetime import datetime
from collections import deque

logger = structlog.get_logger(__name__)

class TelemetryEngine:
    """
    A non-blocking telemetry engine.
    In a real system, this could write to a timeseries DB or Kafka.
    Here we simulate flushing metrics to a local file/logger and aggregate
    stats in memory for the monitoring endpoint.
    """
    def __init__(self):
        self.queue = None
        self.worker_task = None
        self.metrics = {
            "total_queries": 0,
            "failed_queries": 0,
            "empty_retrievals": 0,
            "idk_responses": 0,
            "retrieval_latencies": deque(maxlen=1000),
            "llm_latencies": deque(maxlen=1000),
            "total_latencies": deque(maxlen=1000)
        }

    async def _worker(self):
        while True:
            try:
                event = await self.queue.get()
                # Simulate I/O bound insert
                await asyncio.sleep(0.01)
                
                # Aggregate if it's a RAG trace
                if event["event_type"] == "rag_trace":
                    meta = event["metadata"]
                    self.metrics["total_queries"] += 1
                    if meta.get("failed"):
                        self.metrics["failed_queries"] += 1
                    if meta.get("retrieved_chunks_count", 0) == 0:
                        self.metrics["empty_retrievals"] += 1
                    if meta.get("is_idk"):
                        self.metrics["idk_responses"] += 1
                        
                    if "retrieval_latency" in meta:
                        self.metrics["retrieval_latencies"].append(meta["retrieval_latency"])
                    if "llm_latency" in meta:
                        self.metrics["llm_latencies"].append(meta["llm_latency"])
                    if "total_latency" in meta:
                        self.metrics["total_latencies"].append(meta["total_latency"])
                
                logger.info("TELEMETRY_LOG", event_type=event["event_type"], metadata=event["metadata"])
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
            
    def get_aggregated_stats(self) -> dict:
        def avg(d: deque):
            return sum(d) / len(d) if len(d) > 0 else 0.0
            
        return {
            "total_queries": self.metrics["total_queries"],
            "failed_queries": self.metrics["failed_queries"],
            "empty_retrievals": self.metrics["empty_retrievals"],
            "idk_responses": self.metrics["idk_responses"],
            "avg_retrieval_latency_sec": avg(self.metrics["retrieval_latencies"]),
            "avg_llm_latency_sec": avg(self.metrics["llm_latencies"]),
            "avg_total_latency_sec": avg(self.metrics["total_latencies"])
        }

# Global instance
telemetry = TelemetryEngine()
