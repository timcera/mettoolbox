# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function

import warnings

import pandas as pd
from tstoolbox import tsutils

from . import evaplib

warnings.filterwarnings("ignore")


def et0_pm(
    input_ts="-",
    columns=None,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
    names=None,
    source_units=None,
    target_units=None,
    print_input=False,
    tablefmt="csv",
    avp=None,
    avp_from_tdew=None,
    avp_from_twet_tdry=None,
    avp_from_rhmin_rh_max=None,
    avp_from_tmin=None,
    lat=None,
):
    """Penman-Monteith reference evaporation."""
    tsd = tsutils.common_kwds(
        tsutils.read_iso_ts(
            input_ts, skiprows=skiprows, names=names, index_type=index_type
        ),
        start_date=start_date,
        end_date=end_date,
        pick=columns,
        round_index=round_index,
        dropna=dropna,
        source_units=source_units,
        target_units=target_units,
        clean=clean,
    )

    return tsd
