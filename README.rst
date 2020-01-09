==========
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

Requirements
------------
* pandas - on Windows this is part scientific Python distributions like
  Python(x,y), Anaconda, or Enthought.

* mando - command line parser

Installation
------------
Should be as easy as running ``pip install mettoolbox`` or ``easy_install
mettoolbox`` at any command line.  Not sure on Windows whether this will bring
in pandas, but as mentioned above, if you start with scientific Python
distribution then you shouldn't have a problem.

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

* Free software: BSD license
