mettoolbox
==========

.. image:: https://badge.fury.io/py/mettoolbox.png
    :target: http://badge.fury.io/py/mettoolbox

.. image:: https://travis-ci.org/timcera/mettoolbox.png?branch=master
        :target: https://travis-ci.org/timcera/mettoolbox

.. image:: https://pypip.in/d/mettoolbox/badge.png
        :target: https://crate.io/packages/mettoolbox?version=latest

The mettoolbox is set of command line and Python tools for the analysis and
calculation of meteorologic data.

Installation
------------
Should be as easy as running ``pip install mettoolbox`` or ``easy_install
mettoolbox`` at any command line.

Usage - Command Line
--------------------
Just run 'mettoolbox --help' to get a list of subcommands::

    usage: mettoolbox [-h] [-v] {disaggregate,pet} ...

    positional arguments:
      {disaggregate,pet}
        disaggregate      disaggregate subcommand
        pet               pet subcommand

    optional arguments:
      -h, --help          show this help message and exit
      -v, --version       show program's version number and exit

Usage - Python
--------------
::

    from mettoolbox import mettoolbox
    df = mettoolbox.disaggregate.temperature('sine_min_max', ['degC', 'degC'], temp_min_col=1, temp_max_col=2)
