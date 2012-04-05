#!/usr/bin/env python

from setuptools import setup

setup(

    name='0x10c-asm',
    version='0.0.1',
    description="A simple Python-based DCPU assembly compiler",
    long_description=open('README.rst').read(),
    keywords='notch asm dcpu-16 dcpu assembly asm',
    author='Sever Banesiu',
    author_email='banesiu.sever@gmail.com',
    url='https://github.com/severb/graypy',
    license='BSD License',
    scripts=['0x10-asm.py'],
    zip_safe=False,

)
