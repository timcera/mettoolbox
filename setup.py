# -*- coding: utf-8 -*-

import os
import sys

from setuptools import find_packages, setup

pkg_name = "mettoolbox"

version = open("VERSION").readline().strip()

if sys.argv[-1] == "publish":
    os.system("cleanpy .")
    os.system("python setup.py sdist")
    os.system("twine upload dist/{pkg_name}-{version}.tar.gz".format(**locals()))
    sys.exit()

README = open("README.rst").read()

install_requires = [
    # List your project dependencies here.
    # For more details, see:
    # http://packages.python.org/distribute/setuptools.html#declaring-dependencies
    "tstoolbox >= 103.14.9",
    "solarpy",
    "standard-precip",
]

extras_require = {
    "dev": [
        "black",
        "cleanpy",
        "twine",
        "pytest",
        "coverage",
        "flake8",
        "pytest-cov",
        "pytest-mpl",
        "pre-commit",
    ]
}

setup(
    name=pkg_name,
    version=version,
    description="mettoolbox is set of command line and Python tools for the analysis and reporting of meteorological data.",
    long_description=README,
    classifiers=[
        # Get strings from
        # http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Environment :: Console",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="time_series",
    author="Tim Cera, PE",
    author_email="tim@cerazone.net",
    url="http://timcera.bitbucket.io/{pkg_name}/docs/index.html".format(**locals()),
    license="BSD",
    packages=find_packages("src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": ["{pkg_name}={pkg_name}.{pkg_name}:main".format(**locals())]
    },
    test_suite="tests",
    python_requires=">=3.7.1",
)
