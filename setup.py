#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pymedoc',
    version='0.1.0',
    description="Python package for wireless network triggering of Medoc Pathway Thermal Stimulation System",
    long_description="",
    author="Cosan Lab",
    author_email='cosanlab@gmail.com',
    url='https://github.com/ejolly/pymedoc',
    packages=find_packages(include=['pymedoc']),
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='pymedoc',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    test_suite='tests'
)
