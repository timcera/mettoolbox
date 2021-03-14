import warnings

import numpy as np
import pandas as pd

from tstoolbox import tsutils


def _check_temperature_cols(
    temp_min_col=None,
    temp_max_col=None,
    temp_mean_col=None,
    temp_min_required=False,
    temp_max_required=False,
):
    """ Check temperature columns to make sure necessary ones are filled in. """
    if temp_min_col is None and temp_min_required is True:
        raise ValueError(
            tsutils.error_wrapper(
                """
            This evaporation method requires the minimum daily temperature column to be specified with "temp_min_col".""".format(
                    **locals
                )
            )
        )
    if temp_max_col is None and temp_max_required is True:
        raise ValueError(
            tsutils.error_wrapper(
                """
            This evaporation method requires the maximum daily temperature column to be specified with "temp_max_col".""".format(
                    **locals
                )
            )
        )
    if temp_min_col is None or temp_max_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
            If you do not pass a mean daily temperature column in "temp_mean_col"
            you must give both minimum and maximum daily temperatures using
            "temp_min_col" and "temp_max_col".

    You gave {temp_min_col} for "temp_min_col" and
             {temp_max_col} for "temp_max_col". """.format(
                    **locals
                )
            )
        )
    coll_cols = []
    coll_names = []
    for col, name in [
        (temp_min_col, "tmin"),
        (temp_max_col, "tmax"),
        (temp_mean_col, "tmean"),
    ]:
        if col is None:
            continue
        coll_cols.append(col)
        coll_names.append(name)
    return coll_cols, coll_names


def _validate_temperatures(tsd):
    if "tmean" not in tsd.columns:
        if (tsd.tmax <= tsd.tmin).any():
            raise ValueError(
                tsutils.error_wrapper(
                    """
                On the following dates:

        {0},

        minimum temperature values in column "{1}" are greater than or
        equal to the maximum temperature values in column "{2}".""".format(
                        tsd[tsd.tmax <= tsd.tmin].index, temp_min_col, temp_max_col
                    )
                )
            )

        warnings.warn(
            tsutils.error_wrapper(
                """ Since `temp_mean_col` is None, the average daily temperature will be
estimated by the average of `temp_min_col` and `temp_max_col`""".format(
                    **locals()
                )
            )
        )
        tsd["tmean"] = (tsd.tmin + tsd.tmax) / 2.0
    else:
        if (tsd.tmin >= tsd.tmean).any() or (tsd.tmax <= tsd.tmean).any():
            raise ValueError(
                tsutils.error_wrapper(
                    """ On the following dates:

        {0},

        the daily average is either below or equal to the minimum temperature in column {1} or higher or equal to the maximum temperature in column
    {2}.""".format(
                        tsd[tsd.tmin >= tsd.tmean | tsd.tmax <= tsd.tmean],
                        temp_min_col,
                        temp_max_col,
                    )
                )
            )
    return tsd


def declination():
    # 'Roll-out' the distribution from day to day.
    jday = np.arange(1, 367)

    # FAO declination calculation
    dec = 0.409 * np.sin(2.0 * np.pi * jday / 365.0 - 1.39)

    return dec


def radiation(tsd, lat):
    # 'Roll-out' the distribution from day to day.
    jday = np.arange(1, 367)
    lrad = lat * np.pi / 180.0

    dec = declination()

    s = np.arccos(-np.tan(dec) * np.tan(lrad))

    # FAO radiation calculation
    dr = 1.0 + 0.033 * np.cos(2 * np.pi * jday / 365)

    # FAO radiation calculation
    ra = (
        118.08
        / np.pi
        * dr
        * (s * np.sin(lrad) * np.sin(dec) + np.cos(lrad) * np.cos(dec) * np.sin(s))
    )

    # ra just covers 1 year - need to map onto all years...
    newra = pd.DataFrame(0.0, index=tsd.index, columns=["ra"])
    for day in jday:
        newra.loc[newra.index.dayofyear == day, "ra"] = ra[day - 1]
    return newra
