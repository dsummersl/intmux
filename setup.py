from codecs import open
from os import path

from setuptools import setup


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='intmux',
    version='0.8.0',
    author='Dane Summers',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    license='MIT',
    include_package_data=True,
    description='Connect to multiple hosts simultaneously "in tmux" via ssh and docker.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='ssh tmux docker cli mosh',
    url='https://github.com/dsummersl/intmux',
    python_requires='>=3',
    py_modules=[],
    install_requires=[],
    packages=[
        'scripts'
    ],
    entry_points={
        'console_scripts': ['intmux = scripts.intmux:main']
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)
