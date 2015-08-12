#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    'pandas >= 0.8.1',
    'mando >= 0.3.2',
]

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    os.system('python setup.py upload_docs')
    sys.exit()

readme = open('README.rst').read()

version = open("VERSION").readline().strip()

setup(
    name='mettoolbox',
    version=version,
    description='mettoolbox is set of command line and Python tools for the analysis and reporting of meteorological data.',
    long_description=readme,
    author='Tim Cera',
    author_email='tim@cerazone.net',
    url='https://bitbucket.org/timcera/mettoolbox',
    packages=[
        'mettoolbox',
    ],
    package_dir={'mettoolbox': 'mettoolbox'},
    include_package_data=True,
    install_requires=install_requires,
    license="BSD",
    zip_safe=False,
    keywords='mettoolbox',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
      entry_points={
          'console_scripts':
              ['mettoolbox=mettoolbox.mettoolbox:main']
      },
    test_suite='tests',
)
