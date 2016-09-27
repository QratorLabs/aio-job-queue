import asyncio

from . import task, load_scripts, exceptions


class Queue(object):

    def __init__(self, redis, key_prefix='aioredisqueue_', *,
                 main_queue_key=None,
                 fetching_fifo_key=None,
                 payloads_hash_key=None,
                 ack_hash_key=None,
                 task_class=task.Task,
                 lua_sha=None,
                 loop=None):

        if main_queue_key is None:
            main_queue_key = key_prefix + 'queue'

        if fetching_fifo_key is None:
            fetching_fifo_key = key_prefix + 'fetching'

        if payloads_hash_key is None:
            payloads_hash_key = key_prefix + 'payloads'

        if ack_hash_key is None:
            ack_hash_key = key_prefix + 'ack'

        if loop is None:
            loop = asyncio.get_event_loop()

        self._keys = {
            'queue': main_queue_key,
            'fifo': fetching_fifo_key,
            'payload': payloads_hash_key,
            'ack': ack_hash_key,
        }

        self._redis = redis
        self._loop = loop
        self._task_class = task_class
        self._lua_sha = lua_sha if lua_sha is not None else {}

    async def _load_scripts(self):
        for key in load_scripts.__all__:
            name, script = getattr(load_scripts, key)()
            self._lua_sha[name] = await self._redis.script_load(script)

    def _put_pipe(self, task_id, task_payload):
        transaction = self._redis.multi_exec()
        transaction.hset(self._keys['payload'], task_id, task_payload)
        transaction.lpush(self._keys['queue'], task_id)
        return transaction.execute()

    async def _put_lua(self, task_id, task_payload):
        if 'put' not in self._lua_sha:
            await self._load_scripts()

        return await self._redis.evalsha(
            self._lua_sha['put'],
            keys=[self._keys['payload'], self._keys['queue']],
            args=[task_id, task_payload],
        )

    def put(self, task, method='lua'):
        task_id = self._task_class.generate_id()
        task_payload = self._task_class.format_payload(task)

        if method == 'lua':
            return self._put_lua(task_id, task_payload)
        elif method == 'multi':
            return self._put_pipe(task_id, task_payload)
        else:
            raise TypeError('Wrong put method')

    async def _get_nowait(self, ack_info, script='get_nowait_l', key='fifo'):
        if script not in self._lua_sha:
            await self._load_scripts()

        result = await self._redis.evalsha(
            self._lua_sha[script],
            keys=[self._keys[key], self._keys['ack'], self._keys['payload']],
            args=[ack_info],
        )
        if result[0] == 'ok':
            return result[1]
        else:
            raise exceptions.Empty(result[0])

    async def get_nowait(self):
        ack_info = self._task_class.generate_ack_info()

        try:
            return await self._get_nowait(ack_info, 'get_nowait_l', 'fifo')
        except exceptions.Empty:
            pass

        return await self._get_nowait(ack_info, 'get_nowait', 'queue')

    async def get(self, retry_interval=1):
        while self._loop.is_running():
            result = await self._redis.brpoplpush(self._keys['queue'],
                                                  self._keys['fifo'],
                                                  timeout=retry_interval)
            if result is None:
                continue

            try:
                return await self.get_nowait()
            except exceptions.Empty:
                continue

    def _ack_pipe(self, task_id):
        transaction = self._redis.multi_exec()

        transaction.hdel(self._keys['ack'], task_id)
        transaction.hdel(self._keys['payload'], task_id)

        return transaction.execute()

    async def _ack_lua(self, task_id):
        if 'ack' not in self._lua_sha:
            await self._load_scripts()

        return await self._redis.evalsha(
            self._lua_sha['ack'],
            keys=[self._keys['ack'], self._keys['payload']],
            args=[task_id],
        )

    def _ack(self, task_id, method='multi'):
        if method == 'multi':
            return self._ack_pipe(task_id)
        elif method == 'lua':
            return self._ack_lua(task_id)

    async def _fail(self, task_id):
        if 'fail' not in self._lua_sha:
            await self._load_scripts()

        return await self._redis.evalsha(
            self._lua_sha['fail'],
            keys=[self._keys['ack'], self._keys['payload']],
            args=[task_id],
        )

    async def _requeue(self, before=None):
        if 'requeue' not in self._lua_sha:
            await self._load_scripts()

        return await self._redis.evalsha(
            self._lua_sha['requeue'],
            keys=[self._keys['ack'], self._keys['queue']],
            args=[before],
        )
