import pytest
import asyncio
import aioredis
import aioredisqueue


@pytest.mark.asyncio
async def test_invalid_serializer():
    r = await aioredis.create_redis(('localhost', 6379), db=0)
    message = {'a': 1, '2': ['b', [13]]}
    with pytest.raises(NotImplementedError) as excinfo:
        queue = aioredisqueue.queue.Queue(r, serialization_method='crap')
        await queue.put(message)
        task = await queue.get()

serializers = ['raw', 'json', 'pickle']
try:
    import yaml
    serializers.append('yaml')
except ImportError:
    pass

@pytest.mark.asyncio
@pytest.mark.parametrize('method', serializers)
async def test_queue_specified_serializers(method):
    r = await aioredis.create_redis(('localhost', 6379), db=0)
    message = {'a': 1, '2': ['b', [13]]} if method != 'raw' else b'string'
    queue = aioredisqueue.queue.Queue(r, serialization_method=method)
    await queue.put(message)
    task = await queue.get()
    assert task.payload == message


@pytest.mark.asyncio
@pytest.mark.parametrize('method', serializers)
async def test_task_specified_serializers(method):
    r = await aioredis.create_redis(('localhost', 6379), db=0)
    queue = aioredisqueue.queue.Queue(r)
    message = {'a': 1, '2': ['b', [13]]} if method != 'raw' else b'string'
    await queue.put(message, serialization_method=method)
    task = await queue.get()
    assert task.payload == message
