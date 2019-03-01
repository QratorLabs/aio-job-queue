import os.path

from setuptools import setup, find_packages


setup(
    name='aioredisqueue',
    version='0.1a',
    author='Konstantin Ignatov',
    author_email='kv@qrator.net',
    packages=find_packages(),
    install_requires=(
        'aioredis',
    ),
    package_data={'aioredisqueue': (
        os.path.join('lua', '*' + os.path.extsep + 'lua'),
    )},
)
