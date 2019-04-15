import timeit
import uuid
from .serializers import get_serializer


class Task(object):
    _api_version = 0
    _old_api_loaders = {}
    __slots__ = ('_queue', 'id', 'payload', 'ack_info', 'status', '__weakref__')

    @staticmethod
    def generate_ack_info():
        return int(timeit.default_timer() * 1000)

    @staticmethod
    def generate_id(serialization_method):
        return str(uuid.uuid4()) + '_' + serialization_method

    @staticmethod
    def encode_payload(payload, serialization_method):
        dump = get_serializer(serialization_method)['dump']
        return dump(payload)
    
    @staticmethod
    def decode_payload(task_id, payload):
        task_id = task_id.decode('utf-8')
        serializer_index = task_id.find('_') + 1
        if serializer_index:
            serialization_method = task_id[task_id.find('_') + 1:]
            load = get_serializer(serialization_method)['load']
            return load(payload)
        else: # Compatibility with old versions with raw payload
            return payload
    
    def __init__(self, queue, task_id, payload, ack_info, *, status=1):
        self._queue = queue
        self.id = task_id
        self.payload = payload
        self.ack_info = ack_info
        self.status = 1

    def ack(self):
        self.status = 0
        return self._queue._ack(self.id)

    def fail(self):
        self.status += 1
        return self._queue._fail(self.id)

    def __repr__(self):
        return '<Task %s>' % self.id

    def __getstate__(self):
        return (self._api_version,
                self._queue,
                self.id,
                self.payload,
                self.ack_info,
                self.status)

    def __setstate__(self, state):
        api_version, *data = state

        if api_version == self._api_version:
            (self._queue,
             self.id,
             self.payload,
             self.ack_info,
             self.status) = data
        else:
            self._old_api_loaders[api_version](data)
