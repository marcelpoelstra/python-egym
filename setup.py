#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='python-egym',
    version='1.0',
    description='A python interface for the egym api',
    author='bitstacker',
    author_email='bitstacker@never-afk.de',
    packages=['egym'],
    platforms=['Any'],
    install_requires=['requests'],
    keywords='egym api',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)

