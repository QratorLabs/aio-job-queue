import os.path

import pkg_resources


__all__ = ('load_put', 'load_ack', 'load_fail', 'load_requeue',
           'load_get_nowait', 'load_get_nowait_l')


def _load(name):
    filename = name + os.extsep + 'lua'
    try:
        path = os.path.join('lua', filename)
        return name, pkg_resources.resource_string('aioredisqueue', path)
    except FileNotFoundError:
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, 'lua', filename), 'rb') as fobj:
            return name, fobj.read()

def load_put():
    return _load('put')


def load_ack():
    return _load('ack')


def load_fail():
    return _load('fail')


def load_requeue():
    return _load('requeue')


def load_get_nowait():
    return _load('get_nowait')


def load_get_nowait_l():
    return _load('get_nowait_l')
