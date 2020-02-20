#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import mando
from mando import Program

program = Program("mettoolbox", "0.0")

program.add_subprog("disaggregate")


def main():
    """ Main """
    if not os.path.exists("debug_mettoolbox"):
        sys.tracebacklimit = 0
    program()


if __name__ == "__main__":
    main()
