import asyncio
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Any
from datetime import datetime, timedelta
from loguru import logger


@dataclass
class CommitBatch:
    """Batch of messages to commit together."""
    messages: List[dict]
    created_at: datetime
    futures: List[asyncio.Future] = field(default_factory=list)


class GroupCommitBuffer:
    """
    Buffers messages and commits in batches to reduce I/O.
    
    Inspired by database group commit: coalesce multiple writes
    into a single disk flush.
    """
    
    def __init__(
        self,
        commit_fn: Callable[[List[dict]], Any],
        max_batch_size: int = 50,
        max_latency_ms: float = 100.0,
        min_batch_size: int = 5
    ):
        self.commit_fn = commit_fn
        self.max_batch_size = max_batch_size
        self.max_latency = timedelta(milliseconds=max_latency_ms)
        self.min_batch_size = min_batch_size
        
        self._buffer: List[dict] = []
        self._futures: List[asyncio.Future] = []
        self._lock = asyncio.Lock()
        self._commit_task: Optional[asyncio.Task] = None
        self._last_commit = datetime.now()
        self._running = False
    
    async def start(self) -> None:
        """Start the commit loop."""
        self._running = True
        self._commit_task = asyncio.create_task(self._commit_loop())
    
    async def stop(self) -> None:
        """Stop and flush remaining messages."""
        self._running = False
        if self._commit_task:
            await self._flush()
            self._commit_task.cancel()
            try:
                await self._commit_task
            except asyncio.CancelledError:
                pass
    
    async def add(self, message: dict) -> asyncio.Future:
        """
        Add message to batch.
        
        Returns:
            Future that completes when message is committed
        """
        future = asyncio.Future()
        
        async with self._lock:
            self._buffer.append(message)
            self._futures.append(future)
            
            if len(self._buffer) >= self.max_batch_size:
                asyncio.create_task(self._flush())
        
        return future
    
    async def _commit_loop(self) -> None:
        """Periodic commit based on latency."""
        while self._running:
            await asyncio.sleep(0.01)
            
            async with self._lock:
                if not self._buffer:
                    continue

                elapsed = datetime.now() - self._last_commit
                
                should_commit = (
                    elapsed >= self.max_latency or
                    (len(self._buffer) >= self.min_batch_size and elapsed >= timedelta(milliseconds=10))
                )
                
                if should_commit:
                    await self._do_commit()
    
    async def _flush(self) -> None:
        """Flush current buffer."""
        async with self._lock:
            if self._buffer:
                await self._do_commit()
    
    async def _do_commit(self) -> None:
        """Perform the actual commit."""
        if not self._buffer:
            return
        
        messages = self._buffer.copy()
        futures = self._futures.copy()
        
        self._buffer.clear()
        self._futures.clear()
        self._last_commit = datetime.now()
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.commit_fn, messages
            )
            
            for future in futures:
                if not future.done():
                    future.set_result(True)
            
            logger.debug(f"Group commit: {len(messages)} messages")
            
        except Exception as e:
            logger.error(f"Group commit failed: {e}")
            for future in futures:
                if not future.done():
                    future.set_exception(e)
    
    @property
    def buffer_size(self) -> int:
        """Current number of messages in buffer."""
        return len(self._buffer)
