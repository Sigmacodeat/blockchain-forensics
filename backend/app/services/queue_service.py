"""
Async Queue Service for background processing
"""

import asyncio
import logging
import json
from typing import Dict, Any, Callable, List
import time
import os

logger = logging.getLogger(__name__)

class AsyncQueueService:
    """Simple async queue for background processing."""

    def __init__(self):
        self.enabled = True
        self.queue: asyncio.Queue = asyncio.Queue()
        self.workers = []
        self.worker_count = int(os.getenv("QUEUE_WORKERS", "2"))
        self._running = False

    async def start(self):
        """Start queue workers."""
        if self._running:
            return

        self._running = True
        self.workers = []

        for i in range(self.worker_count):
            worker = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self.workers.append(worker)

        logger.info(f"✅ Async queue started with {self.worker_count} workers")

    async def stop(self):
        """Stop queue workers."""
        self._running = False

        # Wait for workers to finish
        for worker in self.workers:
            worker.cancel()

        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("✅ Async queue stopped")

    async def enqueue(self, task_type: str, payload: Dict[str, Any], callback: Callable = None):
        """Add task to queue."""
        task = {
            "id": f"{task_type}_{int(time.time())}_{id(payload)}",
            "type": task_type,
            "payload": payload,
            "callback": callback,
            "created_at": time.time()
        }

        await self.queue.put(task)
        logger.debug(f"Task {task['id']} enqueued")

    async def _worker_loop(self, worker_id: str):
        """Worker loop for processing tasks."""
        while self._running:
            try:
                # Wait for task with timeout
                try:
                    task = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                logger.debug(f"Worker {worker_id} processing task {task['id']}")

                # Process task
                try:
                    await self._process_task(task)
                    if task.get("callback"):
                        await task["callback"](task)
                except Exception as e:
                    logger.error(f"Task {task['id']} failed: {e}")
                finally:
                    self.queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)  # Brief pause on error

    async def _process_task(self, task: Dict[str, Any]):
        """Process a single task."""
        task_type = task["type"]
        payload = task["payload"]

        if task_type == "ocr_processing":
            await self._process_ocr_task(payload)
        elif task_type == "vision_analysis":
            await self._process_vision_task(payload)
        elif task_type == "kb_reindex":
            await self._process_kb_reindex_task(payload)
        else:
            logger.warning(f"Unknown task type: {task_type}")

    async def _process_ocr_task(self, payload: Dict[str, Any]):
        """Process OCR task."""
        file_path = payload.get("file_path")
        if file_path and os.path.exists(file_path):
            from app.services.ocr_service import ocr_service
            result = await ocr_service.extract_text(file_path, payload.get("mime_type", ""))
            logger.info(f"OCR task completed for {file_path}: {result.get('status')}")

    async def _process_vision_task(self, payload: Dict[str, Any]):
        """Process Vision API task."""
        file_path = payload.get("file_path")
        if file_path and os.path.exists(file_path):
            from app.services.vision_service import vision_service
            result = await vision_service.extract_text_and_entities(file_path)
            logger.info(f"Vision task completed for {file_path}: {result.get('status')}")

    async def _process_kb_reindex_task(self, payload: Dict[str, Any]):
        """Process KB reindex task."""
        root_path = payload.get("root_path")
        if root_path:
            from app.kb.indexer import reindex_kb
            result = await reindex_kb(root_path)
            logger.info(f"KB reindex task completed for {root_path}: {result}")

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": self.queue.qsize(),
            "workers": self.worker_count,
            "running": self._running
        }

# Global queue service instance
queue_service = AsyncQueueService()
