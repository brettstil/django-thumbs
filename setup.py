#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import os

README = os.path.join(os.path.dirname(__file__), 'README.rst')

setup(
    name='django-thumbs',
    version='0.4.1',
    description='The easiest way to create thumbnails for your images with Django. Works with any storage backend.',
    author='Antonio Melé',
    author_email='antonio.mele@gmail.com',
    long_description=open(README, 'r').read(),
    py_modules=['thumbs'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    url='https://github.com/brettstil/django-thumbs',
)
