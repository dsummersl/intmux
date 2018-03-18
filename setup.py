from codecs import open
from os import path

from setuptools import setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='sshmux',
    version='0.2.0',
    author='Dane Summers',
    license='MIT',
    include_package_data=True,
    description='SSH to multiple hosts simultaneously with tmux.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='ssh tmux',
    url='https://github.com/dsummersl/sshmux',
    py_modules=[],
    install_requires=[],
    packages=[
        'scripts'
    ],
    entry_points={
        'console_scripts': [
          'sshmux = scripts.sshmux:main'
        ]
    }
)
