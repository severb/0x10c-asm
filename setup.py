#!/usr/bin/env python

from setuptools import setup

setup(

    name='0x10c-asm',
    version='0.0.2',
    description="A simple Python-based DCPU assembly compiler",
    long_description=open('README.rst').read(),
    keywords='notch asm dcpu-16 dcpu assembly asm',
    author='Sever Banesiu',
    author_email='banesiu.sever@gmail.com',
    url='https://github.com/severb/0x10c-asm',
    license='BSD License',
    scripts=['0x10c-asm.py'],
    zip_safe=False,

)
