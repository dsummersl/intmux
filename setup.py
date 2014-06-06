try:
  from setuptools import setup
except:
  from distutils.core import setup

setup(name='sshmux',
      version='0.1',
      py_modules=[],
      install_requires=[ ],
      packages=[
        'scripts'
      ],
      entry_points={
        'console_scripts': [
          'sshmux = scripts.sshmux:main'
        ]
      }
)
