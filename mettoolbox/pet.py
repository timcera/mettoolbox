#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from typing import Optional, Union
import warnings

import numpy as np
import pandas as pd
import typic

# import pyeto

from tstoolbox import tsutils

from . import evaplib
from . import utils

warnings.filterwarnings("ignore")


def _columns(tsd, req_column_list=[], optional_column_list=[]):
    if None in req_column_list:
        raise ValueError(
            tsutils.error_wrapper(
                """
You need to supply the column (name or number, data column numbering
starts at 1) for {0} time-series.

Instead you gave {1}""".format(
                    len(req_column_list), req_column_list
                )
            )
        )

    collect = []
    for loopvar in req_column_list + optional_column_list:
        try:
            nloopvar = int(loopvar) - 1
        except TypeError:
            nloopvar = loopvar

        if nloopvar is None:
            collect.append(None)
        else:
            collect.append(tsd.ix[:, nloopvar])

    return collect


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
    avp_from_rhmax=None,
    avp_from_rhmean=None,
    avp_from_tmin=None,
    lat=None,
):
    """Penman-Monteith evaporation."""
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


@typic.constrained(ge=-90, le=90)
class FloatLatitude(float):
    """ -90 <= float <= 90 """


@typic.al
def hargreaves(
    lat: FloatLatitude,
    temp_min_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    temp_max_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    temp_mean_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    source_units=None,
    input_ts="-",
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
    names=None,
    target_units=None,
    print_input=False,
):
    """hargreaves"""
    columns, column_names = utils._check_temperature_cols(
        temp_min_col=temp_min_col,
        temp_max_col=temp_max_col,
        temp_mean_col=temp_mean_col,
        temp_min_required=True,
        temp_max_required=True,
    )

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
        clean=clean,
    )

    tsd.columns = column_names

    tsd = utils._validate_temperatures(tsd)

    newra = utils.radiation(tsd, lat)

    tsdiff = tsd.tmax - tsd.tmin

    # Create new dataframe with tsd.index as index in
    # order to get all of the time components correct.
    pe = pd.DataFrame(0.0, index=tsd.index, columns=["pet_hargreaves:mm"])
    pe["pet_hargreaves:mm"] = (
        0.408 * 0.0023 * newra.ra * (tsd.tmean + 17.8) * np.sqrt(abs(tsdiff))
    )
    if target_units != source_units:
        pe = tsutils.common_kwds(pe, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pe)


@typic.al
def oudin(
    lat: FloatLatitude,
    temp_min_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    temp_max_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    temp_mean_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    source_units=None,
    input_ts="-",
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
    names=None,
    target_units=None,
    print_input=False,
):
    """oudin"""
    columns, column_names = utils._check_temperature_cols(
        temp_min_col=temp_min_col,
        temp_max_col=temp_max_col,
        temp_mean_col=temp_mean_col,
    )

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
        clean=clean,
    )

    tsd.columns = column_names

    tsd = utils._validate_temperatures(tsd)

    newra = utils.radiation(tsd, lat)

    # Create new dataframe with tsd.index as index in
    # order to get all of the time components correct.
    pe = pd.DataFrame(0.0, index=tsd.index, columns=["pet_oudin:mm"])

    gamma = 2.45  # the latent heat flux (MJ kg−1)
    rho = 1000.0  # density of water (kg m-3)

    pe.loc[tsd.tmean > -5.0, "pet_oudin:mm"] = (
        newra.ra / (gamma * rho) * (tsd.tmean + 5.0) / 100 * 1000
    )

    if target_units != source_units:
        pe = tsutils.common_kwds(pe, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pe)


def reference():
    """reference penman-monteith"""
    print("reference")


def potential():
    """potential"""
    print("potential")
