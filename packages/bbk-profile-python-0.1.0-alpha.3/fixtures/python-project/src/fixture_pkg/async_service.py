"""Async and process signals for resolver fixtures."""

import asyncio
from concurrent.futures import ProcessPoolExecutor


async def fetch_many(values: list[int]) -> list[int]:
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(asyncio.sleep(0, result=value)) for value in values]
    return [task.result() for task in tasks]


def process_sum(values: list[int]) -> int:
    with ProcessPoolExecutor(max_workers=1) as pool:
        return pool.submit(sum, values).result(timeout=5)
