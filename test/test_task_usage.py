import pytest
import asyncio
import aioredis
import aioredisqueue


@pytest.mark.asyncio
async def test_basic_put_get_and_get():
	r = await aioredis.create_redis(('localhost', 6379), db=0)
	queue = aioredisqueue.queue.Queue(r)
	
	message = 'payload string 1'
	await queue.put(message)
	result = await queue.get()
	assert result.payload == message

	
async def get_ack(queue):
	task = await queue.get()
	await asyncio.sleep(2)
	await task.ack()


async def get_fail_ack(queue):
	task = await queue.get()
	await asyncio.sleep(0.5)
	await task.fail()
	task = await queue.get()
	await asyncio.sleep(0.5)
	await task.fail()
	task = await queue.get()
	await asyncio.sleep(0.5)
	await task.ack()


@pytest.mark.asyncio
async def test_ack():
	r = await aioredis.create_redis(('localhost', 6379), db=0)
	queue = aioredisqueue.queue.Queue(r)
	
	message = 'payload string 2'
	await queue.put(message)
	await get_ack(queue)


@pytest.mark.asyncio
async def test_fail_ack():
	r = await aioredis.create_redis(('localhost', 6379), db=0)
	queue = aioredisqueue.queue.Queue(r)
	
	message = 'payload string 3'
	await queue.put(message)
	await get_fail_ack(queue)
