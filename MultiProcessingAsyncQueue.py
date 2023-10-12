import multiprocessing as mp
import asyncio
from queue import Empty as QueueEmpty
from Async import Loop
from typing import Callable


class MultiProcessingAsyncQueue:
    """
    Processes messages from multiple processes to an async loop for being processed
    """
    def __init__(self, loop:'Loop', consumer_func:Callable):
        self._loop = loop
        self._mp_queue = mp.Manager().Queue()
        self._async_queue = asyncio.Queue()
        self._loop.create_task(self._mp_queue_to_async_queue())
        self._loop.create_task(self._async_process_messages(consumer_func))
        self._lock = mp.Lock()

    async def _mp_queue_to_async_queue(self):
        """
        Puts messages from multiple processes to the async loop of UI to be printed out
        """
        while True:
            try:
                message = self._mp_queue.get_nowait()
            except QueueEmpty:
                await asyncio.sleep(0)
                continue
            except BrokenPipeError:
                break
            await self._async_queue.put(message)

    async def _async_process_messages(self, func:Callable):
        while True:
            async_message = await self._async_queue.get()
            if async_message is None:
                break
            with self._lock:
                func(async_message)

    @property
    def mp_queue(self):
        return self._mp_queue

    @property
    def async_queue(self):
        return self._async_queue

    @property
    def lock(self):
        return self._lock

