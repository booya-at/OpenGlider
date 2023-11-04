import asyncio
import multiprocessing
import logging
from typing import Any
from collections.abc import Coroutine

logger = logging.getLogger(__name__)


class AsyncTaskQueue:
    poll_interval = 0.1
    
    def __init__(self, num_workers: int=None):
        if num_workers is None:
            num_workers = multiprocessing.cpu_count()
            
        self.tasks: list[asyncio.Task] = []
        self.tasks_todo: list[Coroutine] = []
        self.results: list[Any] = []
        self.num_workers = num_workers
    
    @property
    def is_full(self) -> bool:
        return len(self.tasks) >= self.num_workers
    
    def start_task(self, coroutine: Coroutine) -> None:
        task: asyncio.Task = asyncio.ensure_future(coroutine)
        self.tasks.append(task)
        task.add_done_callback(self.done_callback)

    async def add(self, coroutine: Coroutine, wait: bool=True) -> None:
        if wait:
            while self.is_full:
                await asyncio.sleep(self.poll_interval)
        elif self.is_full:
            # store for later (end of another task)
            self.tasks_todo.append(coroutine)
            return
        
        self.start_task(coroutine)        
    
    def done_callback(self, task: asyncio.Task) -> None:
        logger.info(f"finished {task}")

        self.tasks.remove(task)
        self.results.append(task.result())

        if len(self.tasks_todo):
            coroutine = self.tasks_todo.pop()
            self.start_task(coroutine)
    
    async def finish(self) -> list[Any]:
        while len(self.tasks) > 0:
            await asyncio.sleep(self.num_workers)
        
        return self.results