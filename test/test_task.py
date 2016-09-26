import collections
import pickle
import copy


from aioredisqueue import task


def test_ack_info():
    info = task.Task.generate_ack_info()
    assert info > 0
    assert isinstance(info, int)


def make_task_params():
    return collections.OrderedDict((
        ('queue', {}),
        ('task_id', 42),
        ('payload', b'task_payload'),
        ('ack_info', 420),
    ))


def assert_fields(obj, params):
    assert obj._queue is params['queue']
    assert obj.id is params['task_id']
    assert obj.ack_info is params['ack_info']
    assert obj.payload is params['payload']


def assert_fields_eq(obj, params):
    assert obj._queue == params['queue']
    assert obj.id == params['task_id']
    assert obj.ack_info == params['ack_info']
    assert obj.payload == params['payload']


def test_creates_kwargs():
    params = make_task_params()

    obj = task.Task(**params)

    assert_fields(obj, params)


def test_creates_args():
    params = make_task_params()

    obj = task.Task(*params.values())

    assert_fields(obj, params)


def test_copies():
    params = make_task_params()

    obj = task.Task(**params)

    obj_copy = copy.copy(obj)
    obj_deep = copy.deepcopy(obj)

    obj_pick = pickle.loads(pickle.dumps(obj))

    assert_fields(obj_copy, params)
    assert_fields_eq(obj_deep, params)
    assert_fields_eq(obj_pick, params)
