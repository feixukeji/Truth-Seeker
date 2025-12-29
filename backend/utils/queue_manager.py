"""
Request Queue Manager
Implements backend request queuing to ensure API rate limits are respected.
"""

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, Optional

from config import queue_config
from utils.logger import logger


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """Task object"""
    id: str
    payload: Any
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    position: int = 0


class QueueManager:
    """
    Asynchronous Task Queue Manager
    Ensures tasks are executed sequentially, respecting API rate limits.
    """
    
    def __init__(self, max_queue_size: int = None):
        if max_queue_size is None:
            max_queue_size = queue_config.MAX_QUEUE_SIZE
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._tasks: Dict[str, Task] = {}
        self._worker_running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._processor: Optional[Callable[[Any], Coroutine[Any, Any, Any]]] = None
        self._worker_timeout = queue_config.WORKER_TIMEOUT
        
        logger.debug("queue", "Queue manager initialized", {
            "max_queue_size": max_queue_size,
            "worker_timeout": self._worker_timeout,
        })
    
    def set_processor(self, processor: Callable[[Any], Coroutine[Any, Any, Any]]):
        """Set task processing function"""
        self._processor = processor
        logger.debug("queue", "Task processor set")
    
    async def start_worker(self):
        """Start background worker"""
        if self._worker_running:
            logger.debug("queue", "Worker already running")
            return
        
        self._worker_running = True
        self._worker_task = asyncio.create_task(self._worker_loop())
        logger.info("queue", "Background worker started")
    
    async def stop_worker(self):
        """Stop background worker"""
        logger.info("queue", "Stopping background worker...")
        self._worker_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("queue", "Background worker stopped")
    
    async def _worker_loop(self):
        """Worker main loop"""
        logger.debug("queue", "Worker loop started")
        
        while self._worker_running:
            try:
                # Wait for task
                task_id = await asyncio.wait_for(
                    self._queue.get(),
                    timeout=self._worker_timeout
                )
                
                task = self._tasks.get(task_id)
                if not task:
                    logger.warning("queue", f"Task not found: {task_id[:8]}...")
                    continue
                
                # Update task status
                task.status = TaskStatus.PROCESSING
                logger.task_status("queue", task_id, "PROCESSING", "Started processing")
                
                start_time = time.time()
                
                try:
                    if self._processor:
                        result = await self._processor(task.payload)
                        task.result = result
                        task.status = TaskStatus.COMPLETED
                        
                        elapsed_ms = (time.time() - start_time) * 1000
                        logger.task_status("queue", task_id, "COMPLETED", f"Duration {elapsed_ms:.2f}ms")
                    else:
                        task.error = "No processor configured"
                        task.status = TaskStatus.FAILED
                        logger.error("queue", "Task processor not configured")
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    elapsed_ms = (time.time() - start_time) * 1000
                    logger.task_status("queue", task_id, "FAILED", f"{str(e)[:50]}...")
                    logger.error("queue", f"Task processing failed: {str(e)}", {
                        "task_id": task_id[:8] + "...",
                        "elapsed_ms": f"{elapsed_ms:.2f}",
                        "error_type": type(e).__name__,
                    })
                finally:
                    task.completed_at = datetime.now()
                    self._queue.task_done()
                    
                    # Update positions of other tasks in queue
                    self._update_positions()
                    
                    # Output queue status
                    logger.debug("queue", "Queue status updated", {
                        "queue_size": self._queue.qsize(),
                        "total_tasks": len(self._tasks),
                    })
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.debug("queue", "Worker loop cancelled")
                break
            except Exception as e:
                logger.error("queue", f"Worker loop exception: {e}")
                print(f"Worker error: {e}")
    
    def _update_positions(self):
        """Update queue positions for all pending tasks"""
        pending_tasks = [
            t for t in self._tasks.values()
            if t.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)
        ]
        pending_tasks.sort(key=lambda t: t.created_at)
        for i, task in enumerate(pending_tasks):
            task.position = i + 1
    
    async def submit_task(self, payload: Any) -> Task:
        """
        Submit new task to queue
        
        Args:
            payload: Task data
            
        Returns:
            Created task object
        """
        task_id = str(uuid.uuid4())
        position = self._queue.qsize() + 1
        task = Task(
            id=task_id,
            payload=payload,
            position=position
        )
        
        self._tasks[task_id] = task
        await self._queue.put(task_id)
        
        logger.task_status("queue", task_id, "PENDING", f"Position #{position}")
        logger.debug("queue", "New task submitted", {
            "task_id": task_id[:8] + "...",
            "position": position,
            "queue_size": self._queue.qsize(),
        })
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task status"""
        return self._tasks.get(task_id)
    
    def remove_task(self, task_id: str):
        """Remove completed task (for cleanup)"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                del self._tasks[task_id]
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self._queue.qsize()
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """Clean up old timed-out tasks"""
        now = datetime.now()
        to_remove = []
        
        for task_id, task in self._tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds()
                    if age > max_age_seconds:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self._tasks[task_id]
        
        if to_remove:
            logger.debug("queue", f"Cleaned up {len(to_remove)} old tasks", {
                "remaining_tasks": len(self._tasks),
            })


# Global queue instance
queue_manager = QueueManager()
