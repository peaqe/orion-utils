#!/usr/bin/env python3
"""A setuptools-based script for installing integrade."""
import os

from setuptools import find_packages, setup

_project_root = os.path.abspath(os.path.dirname(__file__))


# Get the long description from the README file
with open(os.path.join(_project_root, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='orionutils',
    version='0.1.5',
    author='Red Hat PEAQE Team',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Quality Assurance',
    ],
    description=(
        'An Apache-licensed Python library that facilitates functional testing of '
        'Ansible Galaxy and related tooling.'
    ),
    extras_require={
        'dev': [
            # For `make lint`
            'flake8',
            'flake8-docstrings',
            'flake8-import-order',
            'flake8-quotes',
            # For `make test`
            'pytest-cov',
        ],
    },
    install_requires=[
        'attrs',
    ],
    license='Apache',
    long_description=long_description,
    packages=find_packages(include=['orionutils*']),
    include_package_data=True,
    url='https://github.com/peaqe/orion-utils/',
)
