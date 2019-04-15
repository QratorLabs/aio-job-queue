import asyncio

from . import task, load_scripts, exceptions


class Queue(object):
    def __init__(self, redis, *, key_prefix=None, 
                 serialization_method='pickle', main_queue_key=None,
                 fetching_fifo_key=None, payloads_hash_key=None,
                 ack_hash_key=None, task_class=task.Task, lua_sha=None,
                 loop=None):
        """
        Redis implementation of asynchronous job queue

        Args :
            serialization_method (str): A string that specifies the way payload
                is encoded and decoded. Default supported serialization method
                s are `raw`, `json`, `pickle` and `dynamic`.

                When using `raw` you must pass binary payload when creating a
                task and be aware of getting it as a result when taking a task
                from queue. `None` as `serialization_method` is the same as
                `raw`.

                `dynamic` method enables to specify `serialization_method` for
                each task, namely as a keyword argument in `put` method
        """
        if serialization_method is None:
            serialization_method = 'raw'

        if key_prefix is None:
            key_prefix = 'aioredisqueue_' + serialization_method

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
        self._locks = {}
        self._serialization_method = serialization_method

    async def _load_scripts(self, primary):
        for key in load_scripts.__all__:
            name, script = getattr(load_scripts, key)()

            if name in self._lua_sha:
                if name == primary:
                    return
                continue

            if name in self._locks:
                if name == primary:
                    async with self._locks[name]:
                        return
                continue

            self._locks[name] = asyncio.Semaphore(0, loop=self._loop)
            try:
                self._lua_sha[name] = await self._redis.script_load(script)
            finally:
                self._locks[name].release()
                del self._locks[name]

    def _put_pipe(self, task_id, task_payload):
        transaction = self._redis.multi_exec()
        transaction.hset(self._keys['payload'], task_id, task_payload)
        transaction.lpush(self._keys['queue'], task_id)
        return transaction.execute()

    async def _put_lua(self, task_id, task_payload):
        if 'put' not in self._lua_sha:
            await self._load_scripts('put')

        return await self._redis.evalsha(
            self._lua_sha['put'],
            keys=[self._keys['payload'], self._keys['queue']],
            args=[task_id, task_payload],
        )

    def put(self, task, serialization_method='pickle', method='lua'):
        if self._serialization_method != 'dynamic':
            serialization_method = self._serialization_method

        task_id = self._task_class.generate_id(serialization_method)
        task_payload = self._task_class.encode_payload(task,
                                                       serialization_method)

        if method == 'lua':
            return self._put_lua(task_id, task_payload)
        elif method == 'multi':
            return self._put_pipe(task_id, task_payload)
        else:
            raise TypeError('Wrong put method')

    async def _get_nowait(self, ack_info, script='get_nowait_l', key='fifo'):
        if script not in self._lua_sha:
            await self._load_scripts(script)

        result = await self._redis.evalsha(
            self._lua_sha[script],
            keys=[self._keys[key], self._keys['ack'], self._keys['payload']],
            args=[ack_info],
        )
        if result[0] == b'ok':
            payload = self._task_class.decode_payload(result[1], result[2])
            return self._task_class(self, result[1], payload, ack_info)
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
            await self._redis.brpoplpush(self._keys['queue'],
                                         self._keys['fifo'],
                                         timeout=retry_interval)
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
            await self._load_scripts('ack')

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
            await self._load_scripts('fail')

        return await self._redis.evalsha(
            self._lua_sha['fail'],
            keys=[self._keys['ack'], self._keys['queue']],
            args=[task_id],
        )

    async def _requeue(self, before=None):
        if 'requeue' not in self._lua_sha:
            await self._load_scripts('requeue')

        return await self._redis.evalsha(
            self._lua_sha['requeue'],
            keys=[self._keys['ack'], self._keys['queue']],
            args=[before],
        )
