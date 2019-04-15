import os.path

from setuptools import find_packages, setup


setup(
    name='aioredisqueue',
    version='0.1a',
    author='Konstantin Ignatov',
    author_email='kv@qrator.net',
    packages=find_packages(),
    install_requires=(
        'aioredis',
    ),
    extras_require={
        'test': ['pytest', 'pytest-asyncio'],
        'yaml-serializer': ['pyyaml']
    },
    package_data={'aioredisqueue': (
        os.path.join('lua', '*' + os.path.extsep + 'lua'),
    )},
)
