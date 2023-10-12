import asyncio


class Loop:
    """

    """
    def __init__(self, top):
        self.top = top
        self._loop = asyncio.get_event_loop()
        self._loop.create_task(self.asyncio_event_loop())

    async def asyncio_event_loop(self, interval=0):
        while True:
            self.top.update()
            await asyncio.sleep(interval)
            _task = asyncio.current_task()
            if _task:
                if _task.cancelled():
                    raise asyncio.CancelledError()

    def __getattr__(self, item):
        return getattr(self._loop, item)

