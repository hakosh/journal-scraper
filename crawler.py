import asyncio
from typing import Callable, Awaitable

import aiohttp

from models import Link, save_link, get_links, count_pending, save_link_status


class Crawler:
    def __init__(
            self,
            repo: str,
            visit: Callable[[aiohttp.ClientSession, Link], Awaitable[list[Link]]],
            concurrency: int
    ):
        self._repo = repo
        self._visit = visit
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)
        self._session = None

        self._pending = dict()

    async def start(self, link: Link):
        save_link(link)
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        )

        while True:
            await asyncio.sleep(1)
            self._poll()

            if len(self._pending) == 0 and count_pending(self._repo) == 0:
                await self._session.close()
                break

    def _enqueue(self, links: list[Link]):
        for link in links:
            save_link(link)

    def _poll(self):
        count = self._concurrency - len(self._pending)
        links = get_links(self._repo, count)
        for link in links:
            task = asyncio.create_task(self._process(link))
            task.add_done_callback(self._done)

            self._pending[task] = link

    async def _process(self, link: Link):
        async with self._semaphore:
            return await self._visit(self._session, link)

    def _done(self, task: asyncio.Task):
        link = self._pending[task]

        exception = task.exception()
        if exception is not None:
            status = "failed"
        else:
            self._enqueue(task.result())
            status = "succeeded"

        del self._pending[task]
        save_link_status(link, status)
