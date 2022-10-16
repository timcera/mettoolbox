.. image:: https://github.com/timcera/mettoolbox/actions/workflows/python-package.yml/badge.svg
    :alt: Tests
    :target: https://github.com/timcera/mettoolbox/actions/workflows/python-package.yml
    :height: 20

.. image:: https://img.shields.io/coveralls/github/timcera/mettoolbox
    :alt: Test Coverage
    :target: https://coveralls.io/r/timcera/mettoolbox?branch=master
    :height: 20

.. image:: https://img.shields.io/pypi/v/mettoolbox.svg
    :alt: Latest release
    :target: https://pypi.python.org/pypi/mettoolbox/
    :height: 20

.. image:: https://img.shields.io/pypi/l/mettoolbox.svg
    :alt: BSD-3 clause license
    :target: https://pypi.python.org/pypi/mettoolbox/
    :height: 20

.. image:: https://img.shields.io/pypi/dd/mettoolbox.svg
    :alt: mettoolbox downloads
    :target: https://pypi.python.org/pypi/mettoolbox/
    :height: 20

.. image:: https://img.shields.io/pypi/pyversions/mettoolbox
    :alt: PyPI - Python Version
    :target: https://pypi.org/project/mettoolbox/
    :height: 20

mettoolbox
==========
The mettoolbox is set of command line and Python tools for the analysis and
calculation of meteorologic data.

Installation
------------
Should be as easy as running ``pip install mettoolbox`` or ``easy_install
mettoolbox`` at any command line.

Usage - Command Line
--------------------
Just run 'mettoolbox --help' to get a list of subcommands::

    usage: mettoolbox [-h] [-v] {disaggregate,pet,ret,indices,about} ...

    positional arguments:
      {disaggregate,pet,ret,indices,about}
        disaggregate        disaggregate subcommand
        pet                 pet subcommand
        ret                 ret subcommand
        indices             indices subcommand
        about               Display version number and system information.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit

Usage - Python
--------------
::

    from mettoolbox import mettoolbox
    df = mettoolbox.disaggregate.temperature('sine_min_max', ['degC', 'degC'], temp_min_col=1, temp_max_col=2)
