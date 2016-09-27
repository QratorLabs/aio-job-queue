from aioredisqueue import load_scripts

import pytest


@pytest.fixture(
    params=load_scripts.__all__,
)
def script_load_func(request):
    return getattr(load_scripts, request.param)


def test_load_script(script_load_func):

    name, script = script_load_func()

    assert script.startswith(b'--')
    assert b'return' in script
