import json
import pickle

_serializers = {
    'json': {
        'load': lambda payload: json.loads(payload.decode('utf-8')),
        'dump': json.dumps
    },
    'pickle': {
        'load': pickle.loads,
        'dump': pickle.dumps
    },
    'raw': {
        'load': lambda payload: payload,
        'dump': lambda message: message
    }
}


def register(name, load, dump):
    _serializers.update({name: {
        'load': load,
        'dump': dump,
    }})


class UnknownSerializationMethod(NotImplementedError):
    def __init__(self, wrong_method, extra_message=None):
        message = """Could not use {} as serialization method. Available options
        are : {}. """
        if extra_message is not None:
            message += + extra_message
        super().__init__(message.format(wrong_method, ', '.join(
            _serializers.keys())))


def get_serializer(serializer_name):
    if serializer_name in _serializers:
        return _serializers[serializer_name]
    else:
        if serializer_name == 'yaml':
            try:
                import yaml
                _serializers.update({'yaml': {
                    'load': lambda payload: yaml.load(payload, Loader=yaml.Loader),
                    'dump': lambda message: yaml.dump(message, Dumper=yaml.Dumper)
                }})
                return _serializers[serializer_name]
            except ImportError:
                raise UnknownSerializationMethod('yaml', 'yaml package not found')
        else:
            raise UnknownSerializationMethod(serializer_name)

