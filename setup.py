#!/usr/bin/env python

from setuptools import setup, find_packages # type: ignore

setup(
    name="plico_io_server",
    version="0.1.0",
    description="PLICO controller server for IO device control",
    author="INAF Arcetri Adaptive Optics",
    author_email="",
    url="",
    packages=find_packages(),
    package_data={
        'plico_io_server': ['conf/plico_io_server.conf'],
    },
    install_requires=[
        'plico',
        'meross_iot',
        'numpy',
        'six',
        'appdirs',
    ],
    entry_points={
        'console_scripts': [
            'plico_io_start=plico_io_server.scripts.io_start:main',
            'plico_io_stop=plico_io_server.scripts.io_stop:main',
            'plico_io_monitor_start=plico_io_server.process_monitor.process_monitor_start:main',
        ],
    }
)