# Reliable queue implementation with Redis backend and python-asyncio client

## Requirements:

- python3.5
- aioredis (we only need `Redis` object with awaitable methods)

## Basic usage:

`Redis` object should be created before `Queue` init. This way you may use the
same connecton to Redis for different purposes in your program.

```
import asyncio
import aioredis
import aioredisqueue

loop = asyncio.get_event_loop()

async def process_jobs():
    redis = await aioredis.create_reconnecting_redis(...)
    queue = aioredisqueue.Queue(redis)
    await q.put(b'abc')

    task = await q.get()
    print(task.payload)

    await task.ack()


loop.run_until_complete(process_jobs)
```

## Non-standard features:

All methods are coroutines, even `get_nowait`. That's because calls to redis are
performed during each such call.

## What can change soon

### API changes
- `loop` may be deleted from constructor params

### New features
- Task classes with built-in serialization support
- `max_items` limit support: current version of `put` method will
  be renamed into `put_nowait`.
- `get_multi` and `put_multi` methods, allowing getting and putting multiple
  items from queue with one call
- method for periodical requeueing of not acknowledged tasks
- keeping track of times a task was requeued, dropping too old tasks or tasks
  with too many retries.
