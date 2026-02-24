from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Callable
from datetime import datetime
import json
from pathlib import Path
from loguru import logger

if TYPE_CHECKING:
    from nanofolks.bus.events import MessageEnvelope
    from nanofolks.storage.cas_storage import CASFileStorage

from nanofolks.models.message_envelope import DEFAULT_PRIORITY
from nanofolks.utils.helpers import ensure_dir, safe_filename
from nanofolks.config.loader import get_data_dir
from nanofolks.metrics import get_metrics


@dataclass
class QueuedMessage:
    """Message in the room queue with sequence number."""
    seq: int
    message: "MessageEnvelope"
    priority: int = DEFAULT_PRIORITY
    received_at: datetime = field(default_factory=datetime.now)
    claimed_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    claimed_by: Optional[str] = None


class RoomMessageBroker:
    """
    Per-room message broker with FIFO guarantees.
    
    Each room has its own queue and can process independently
    of other rooms, enabling parallelism across rooms while
    maintaining strict ordering within a room.
    """
    
    def __init__(
        self, 
        room_id: str,
        storage: Optional["CASFileStorage"] = None,
        agent_loop_factory: Optional[Callable[[], object]] = None,
        max_queue_size: int = 1000,
        enqueue_timeout: float | None = 1.0,
        high_priority_timeout: float | None = 3.0,
        queue_dir: Optional[Path] = None,
    ):
        self.room_id = room_id
        self.storage = storage
        self.agent_loop_factory = agent_loop_factory
        self.agent_loop = None
        self.max_queue_size = max_queue_size
        self.enqueue_timeout = enqueue_timeout
        self.high_priority_timeout = high_priority_timeout

        base_dir = queue_dir or (get_data_dir() / "broker_queue")
        self.queue_dir = ensure_dir(Path(base_dir))
        safe_room = safe_filename(self.room_id)
        self._log_path = self.queue_dir / f"{safe_room}.jsonl"
        self._cursor_path = self.queue_dir / f"{safe_room}.cursor"
        self._metrics = get_metrics()
        
        self._queue: asyncio.PriorityQueue[tuple[int, int, QueuedMessage]] = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._seq_counter = 0
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
        
        self.messages_received = 0
        self.messages_processed = 0
        self.messages_failed = 0
        self.messages_dropped = 0
        self.messages_replayed = 0
    
    def set_agent_loop(self, agent_loop: object) -> None:
        """Set the agent loop for this broker."""
        self.agent_loop = agent_loop
    
    async def enqueue(self, message: "MessageEnvelope") -> bool:
        """
        Add message to room queue.
        
        Args:
            message: Inbound message to queue
            
        Returns:
            True if queued successfully, False if queue full
        """
        priority = getattr(message, "priority", DEFAULT_PRIORITY)
        if message.metadata and "priority" in message.metadata:
            try:
                priority = int(message.metadata["priority"])
            except (TypeError, ValueError):
                pass

        try:
            self._seq_counter += 1
            queued = QueuedMessage(
                seq=self._seq_counter,
                message=message,
                priority=priority,
            )

            timeout = self.enqueue_timeout
            if priority <= 1 and self.high_priority_timeout is not None:
                if timeout is None:
                    timeout = self.high_priority_timeout
                else:
                    timeout = max(timeout, self.high_priority_timeout)

            if timeout is None:
                await self._queue.put((priority, queued.seq, queued))
            else:
                await asyncio.wait_for(self._queue.put((priority, queued.seq, queued)), timeout=timeout)
            self.messages_received += 1
            self._append_to_log(queued)
            self._metrics.incr("broker.message.enqueued", tags={"room": self.room_id})
            self._metrics.set_gauge("broker.queue.depth", self._queue.qsize(), tags={"room": self.room_id})
            
            logger.debug(f"Enqueued message {queued.seq} in room {self.room_id}")
            return True
            
        except (asyncio.QueueFull, asyncio.TimeoutError):
            self.messages_dropped += 1
            self._metrics.incr("broker.message.dropped", tags={"room": self.room_id})
            logger.error(f"Room {self.room_id} queue full, dropping message")
            return False
    
    async def start(self) -> None:
        """Start the broker processing loop."""
        if self.agent_loop_factory and not self.agent_loop:
            self.agent_loop = self.agent_loop_factory()

        await self._replay_pending()
        
        self._running = True
        self._process_task = asyncio.create_task(self._process_loop())
        logger.info(f"Room broker started for {self.room_id}")
    
    async def stop(self) -> None:
        """Stop the broker gracefully."""
        self._running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        logger.info(f"Room broker stopped for {self.room_id}")
    
    async def _process_loop(self) -> None:
        """
        Main processing loop - FIFO order guaranteed.
        
        Processes messages one at a time to maintain ordering.
        Different rooms process in parallel.
        """
        while self._running:
            try:
                _priority, _seq, queued = await asyncio.wait_for(
                    self._queue.get(), 
                    timeout=1.0
                )
                
                queued.claimed_at = datetime.now()
                queued.claimed_by = getattr(self.agent_loop, 'bot_name', 'unknown') if self.agent_loop else 'unknown'
                
                try:
                    await self._process_message(queued)
                    self.messages_processed += 1
                    self._metrics.incr("broker.message.processed", tags={"room": self.room_id})
                except Exception as e:
                    logger.error(f"Failed to process message {queued.seq}: {e}")
                    self.messages_failed += 1
                    self._metrics.incr("broker.message.failed", tags={"room": self.room_id})
                
                queued.processed_at = datetime.now()
                self._write_cursor(queued.seq)
                self._metrics.set_gauge("broker.queue.depth", self._queue.qsize(), tags={"room": self.room_id})
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    def _append_to_log(self, queued: QueuedMessage) -> None:
        """Append a queued message to the room log for crash-safe replay."""
        record = {
            "seq": queued.seq,
            "priority": queued.priority,
            "received_at": queued.received_at.isoformat(),
            "message": queued.message.to_dict(),
        }
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist queue log for room {self.room_id}: {e}")

    def _read_cursor(self) -> int:
        if not self._cursor_path.exists():
            return 0
        try:
            return int(self._cursor_path.read_text().strip() or "0")
        except Exception:
            return 0

    def _write_cursor(self, seq: int) -> None:
        try:
            self._cursor_path.write_text(str(seq))
        except Exception as e:
            logger.warning(f"Failed to update broker cursor for room {self.room_id}: {e}")

    async def _replay_pending(self) -> None:
        """Replay any queued messages from disk after a crash or restart."""
        if not self._log_path.exists():
            return

        last_seq = self._read_cursor()
        pending: list[QueuedMessage] = []
        max_seq = last_seq

        try:
            with open(self._log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    record = json.loads(line)
                    seq = int(record.get("seq", 0))
                    if seq <= last_seq:
                        continue
                    msg_data = record.get("message", {})
                    try:
                        message = msg_data if isinstance(msg_data, dict) else {}
                        from nanofolks.models.message_envelope import MessageEnvelope
                        envelope = MessageEnvelope.from_dict(message)
                        if envelope.room_id:
                            envelope.set_room(envelope.room_id)
                        queued_msg = QueuedMessage(
                            seq=seq,
                            message=envelope,
                            priority=int(record.get("priority", envelope.priority)),
                        )
                        pending.append(queued_msg)
                        max_seq = max(max_seq, seq)
                    except Exception as e:
                        logger.warning(f"Failed to replay queued message in {self.room_id}: {e}")
        except Exception as e:
            logger.warning(f"Failed to read queue log for room {self.room_id}: {e}")
            return

        for queued in pending:
            try:
                await self._queue.put((queued.priority, queued.seq, queued))
                self.messages_replayed += 1
                self._metrics.incr("broker.message.replayed", tags={"room": self.room_id})
            except Exception as e:
                logger.warning(f"Failed to requeue message {queued.seq} for room {self.room_id}: {e}")

        if pending:
            self._seq_counter = max(self._seq_counter, max_seq)
            self._rewrite_log(pending)
            logger.info(f"Replayed {len(pending)} queued messages for room {self.room_id}")

    def _rewrite_log(self, pending: list[QueuedMessage]) -> None:
        """Rewrite log to keep only pending messages (avoid unbounded growth)."""
        try:
            with open(self._log_path, "w", encoding="utf-8") as f:
                for queued in pending:
                    record = {
                        "seq": queued.seq,
                        "priority": queued.priority,
                        "received_at": queued.received_at.isoformat(),
                        "message": queued.message.to_dict(),
                    }
                    f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.warning(f"Failed to rewrite queue log for room {self.room_id}: {e}")
    
    async def _process_message(self, queued: QueuedMessage) -> None:
        """Process a single message through the agent loop."""
        logger.info(
            f"Processing message {queued.seq} in room {self.room_id} "
            f"(queue depth: {self._queue.qsize()})"
        )
        
        if self.agent_loop and hasattr(self.agent_loop, 'process_inbound'):
            await self.agent_loop.process_inbound(queued.message)
        else:
            logger.warning(f"No agent loop configured for room {self.room_id}")
    
    @property
    def queue_depth(self) -> int:
        """Current number of messages waiting."""
        return self._queue.qsize()
    
    @property
    def is_running(self) -> bool:
        """Whether broker is active."""
        return self._running and (self._process_task is not None and not self._process_task.done())


class RoomBrokerManager:
    """
    Manages per-room message brokers.
    
    Routes messages to the correct room broker based on room_id.
    Creates brokers on-demand.
    """
    
    def __init__(
        self, 
        storage: Optional["CASFileStorage"] = None,
        agent_loop_factory: Optional[Callable[[], object]] = None,
        max_queue_size: int = 1000,
        enqueue_timeout: float | None = 1.0,
        high_priority_timeout: float | None = 3.0,
        queue_dir: Optional[Path] = None,
    ):
        self.storage = storage
        self.agent_loop_factory = agent_loop_factory
        self.max_queue_size = max_queue_size
        self.enqueue_timeout = enqueue_timeout
        self.high_priority_timeout = high_priority_timeout
        self.queue_dir = queue_dir
        self._brokers: dict[str, RoomMessageBroker] = {}
        self._lock = asyncio.Lock()
    
    async def route_message(self, message: "MessageEnvelope") -> bool:
        """
        Route message to appropriate room broker.
        
        Args:
            message: Inbound message (must have room_id set)
            
        Returns:
            True if routed successfully
        """
        room_id = message.room_id
        if not room_id:
            logger.error("Cannot route message without room_id")
            return False
        
        async with self._lock:
            if room_id not in self._brokers:
                broker = RoomMessageBroker(
                    room_id=room_id,
                    storage=self.storage,
                    agent_loop_factory=self.agent_loop_factory,
                    max_queue_size=self.max_queue_size,
                    enqueue_timeout=self.enqueue_timeout,
                    high_priority_timeout=self.high_priority_timeout,
                    queue_dir=self.queue_dir,
                )
                await broker.start()
                self._brokers[room_id] = broker
                logger.info(f"Created broker for room {room_id}")
            
            broker = self._brokers[room_id]
        
        return await broker.enqueue(message)
    
    async def stop_all(self) -> None:
        """Stop all room brokers."""
        async with self._lock:
            for room_id, broker in self._brokers.items():
                await broker.stop()
            self._brokers.clear()
    
    def get_stats(self) -> dict:
        """Get stats for all brokers."""
        return {
            room_id: {
                "queue_depth": broker.queue_depth,
                "running": broker.is_running,
                "received": broker.messages_received,
                "processed": broker.messages_processed,
                "failed": broker.messages_failed,
                "dropped": broker.messages_dropped,
                "replayed": broker.messages_replayed,
            }
            for room_id, broker in self._brokers.items()
        }
    
    def get_broker(self, room_id: str) -> Optional[RoomMessageBroker]:
        """Get a broker for a specific room."""
        return self._brokers.get(room_id)
