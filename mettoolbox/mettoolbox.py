#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys
import os.path
import warnings
import itertools
import datetime
from collections import namedtuple

import pandas as pd
import mando
from mando.rst_text_formatter import RSTHelpFormatter
from pysolar.util import mean_earth_sun_distance
import scipy as sp

from tstoolbox import tsutils

warnings.filterwarnings("ignore")

DEG2RAD = pd.np.pi / 180

_LOCAL_DOCSTRINGS = tsutils.docstrings
_LOCAL_DOCSTRINGS[
    "latitude"
] = """latitude:
        The latitude of the location expressed in decimal degrees.  The
        southern hemisphere is expressed as a negative value."""
_LOCAL_DOCSTRINGS[
    "longitude"
] = """longitude:
        The longitude of the location expressed in decimal degrees.  The
        western hemisphere is expressed as a negative value."""
_LOCAL_DOCSTRINGS[
    "vardesc"
] = """If int or float use the value.  If
        array_like, then convert to numpy array.  If string, then split
        on commas and use as array_like.

        If None (the default) then `input_ts` and `columns` must be set."""


from .functions.utils import utils


@mando.command("disaggregate", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def disaggregate_cli(variable, method):
    """Disaggregate daily to hourly meteorological data.

    Parameters
    ==========
    variable:
        The kind of data to disaggregate.  Can be one of "temperature",
        "humidity", "wind", "radiation", and "precipitation".

    method:
        Different methods are available for different variables.

        Temperature
        variable="temperature"
        +---------------------+-------------------------------------+
        | `method`            | Description                         |
        +=====================+=====================================+
        | sine_min_max        | Standard sine redistribution;       |
        |                     | preserves Tmin and Tmax but not     |
        |                     | Tmean.                              |
        +---------------------+-------------------------------------+
        | sine_mean           | Sine redistribution; preserves      |
        |                     | Tmean and the diurnal temperature   |
        |                     | range (Tmax – Tmin) but not Tmin    |
        |                     | and Tmax.                           |
        +---------------------+-------------------------------------+
        | mean_course_min_max | Redistribute following a prescribed |
        |                     | temperature course calculated from  |
        |                     | hourly observations; preserves Tmin |
        |                     | and Tmax.                           |
        +---------------------+-------------------------------------+
        | mean_course_mean    | Redistribute following a prescribed |
        |                     | temperature course calculated from  |
        |                     | hourly observations; preserves      |
        |                     | Tmean and the diurnal temperature   |
        |                     | range.                              |
        +---------------------+-------------------------------------+

        Humidity
        variable="humidity"
        +---------------------------+-------------------------------+
        | `method`                  | Description                   |
        +===========================+===============================+
        | equal                     | Duplicate mean daily humidity |
        |                           | for the 24 hours of the day.  |
        +---------------------------+-------------------------------+
        | minimal                   | The dew point temperature is  |
        |                           | set to the minimum            |
        |                           | temperature on that day.      |
        +---------------------------+-------------------------------+
        | dewpoint_regression       | Using hourly observations, a  |
        |                           | regression approach is        |
        |                           | applied to calculate daily    |
        |                           | dew point temperature.        |
        |                           | Regression parameters must be |
        |                           | specified.                    |
        +---------------------------+-------------------------------+
        | linear_dewpoint_variation | This method extends through   |
        |                           | linearly varying dew point    |
        |                           | temperature between           |
        |                           | consecutive days. The         |
        |                           | parameter kr needs to be      |
        |                           | specified (kr=6 if monthly    |
        |                           | radiation exceeds 100 W/m2    |
        |                           | else kr=12).                  |
        +---------------------------+-------------------------------+
        | min_max                   | This method requires minimum  |
        |                           | and maximum relative humidity |
        |                           | for each day.                 |
        +---------------------------+-------------------------------+
        | month_hour_precip_mean    | Calculate hourly humidity     |
        |                           | from categorical              |
        |                           | [month, hour, precip(y/n)]    |
        |                           | mean values derived from      |
        |                           | observations.                 |
        +---------------------------+-------------------------------+

        Wind Speed
        variable="wind"
        +----------+------------------------------------------------+
        | `method` | Description                                    |
        +==========+================================================+
        | equal    | If this method is chosen, the daily average    |
        |          | wind speed is assumed to be valid for each     |
        |          | hour on that day.                              |
        +----------+------------------------------------------------+
        | cosine   | The cosine function option simulates a diurnal |
        |          | course of wind speed and requires calibration  |
        |          | (calc_wind_stats()).                           |
        +----------+------------------------------------------------+
        | random   | This option is a stochastic method that draws  |
        |          | random numbers to disaggregate wind speed      |
        |          | taking into account the daily average (no      |
        |          | parameter estimation required).                |
        +----------+------------------------------------------------+

        Radiation
        variable="radiation"
        +-----------------+-----------------------------------------+
        | `method`        | Description                             |
        +=================+=========================================+
        | pot_rad         | This method allows one to disaggregate  |
        |                 | daily averages of shortwave radiation   |
        |                 | using hourly values of potential        |
        |                 | (clear-sky) radiation calculated for    |
        |                 | the location of the station.            |
        +-----------------+-----------------------------------------+
        | pot_rad_via_ssd | If daily sunshine recordings are        |
        |                 | available, the Angstrom model is        |
        |                 | applied to transform sunshine duration  |
        |                 | to shortwave radiation.                 |
        +-----------------+-----------------------------------------+
        | pot_rad_via_bc  | In this case, the Bristow-Campbell      |
        |                 | model is applied which relates minimum  |
        |                 | and maximum temperature to shortwave    |
        |                 | radiation.                              |
        +-----------------+-----------------------------------------+
        | mean_course     | hourly radiation follows an observed    |
        |                 | average course (calculated for each     |
        |                 | month) while preserving the daily mean. |
        +-----------------+-----------------------------------------+

        Precipitation
        variable="precipitation"
        +---------------+--------------------------------------------+
        | `method`      | Description                                |
        +===============+============================================+
        | equal         | In order to derive hourly from daily       |
        |               | values, the daily total is simply divided  |
        |               | by 24 resulting in an equal distribution.  |
        +---------------+--------------------------------------------+
        | cascade       | The cascade model is more complex and      |
        |               | requires a parameter estimation method.    |
        +---------------+--------------------------------------------+
        | masterstation | If hourly values are available for another |
        |               | site in the vicinity of the station        |
        |               | considered, the cumulative sub-daily mass  |
        |               | curve can be transferred from the station  |
        |               | that provides hourly values to the station |
        |               | of interest.                               |
        +---------------+--------------------------------------------+

    min_max_time: str
        [required if `variable` is "temperature", otherwise not used]

        +----------------+------------------------------------------+
        | `min_max_time` | Description                              |
        +================+==========================================+
        | fix            | The diurnal course of temperature is     |
        |                | fixed without any seasonal variations.   |
        +----------------+------------------------------------------+
        | sun_loc        | The diurnal course of temperature is     |
        |                | modelled based on sunrise, noon and      |
        |                | sunset calculations.                     |
        +----------------+------------------------------------------+
        | sun_loc_shift  | This option activates empirical          |
        |                | corrections of the ideal course modelled |
        |                | by sun_loc                               |
        +----------------+------------------------------------------+

    mod_nighttime: bool
        [optional if `variable` is "temperature", default is False]

        Allows one to apply a linear interpolation of
        night time values, which proves preferable during polar
        nights.

    """
    tsutils.printiso(disaggregate(variable, method,
                                  min_max_time=min_max_time,
                                  mod_nighttime=mod_nigthtime))


@tsutils.validator(
    variable=[
        str,
        ["domain", ["temperature", "humidity", "wind", "radiation", "precipitation"]],
        1,
    ],
    method=[
        str,
        [
            "domain",
            [
                "sine_min_max",
                "sine_mean",
                "mean_course_min_max",
                "mean_course_mean",
                "equal",
                "minimal",
                "dewpoint_regression",
                "linear_dewpoint_variation",
                "min_max",
                "month_hour_precip_mean",
                "cosine",
                "random",
                "pot_rad",
                "pot_rad_via_ssd",
                "pot_rad_via_bc",
                "mean_course",
                "cascade",
                "masterstation",
            ],
        ],
        1,
    ],
    min_max_time=[str, ["domain", ["fix", "sun_loc", "sun_loc_shift"]], 1],
    mod_nighttime=[bool, ["pass", []], 1],
)
def disaggregate(variable, method, min_max_time=None,
                 mod_nighttime=False):
    pass


disaggregate.__doc__ = disaggregate_cli.__doc__


@mando.command(formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def daily_to_daytime_hourly_trapezoid(
    latitude,
    input_ts="-",
    start_date=None,
    end_date=None,
    float_format="%g",
    print_input="",
):
    """
    Daily to hourly daytime disaggregation based on a trapezoidal shape.

    Parameters
    ----------
    {latitude}
    {input_ts}
    {start_date}
    {end_date}
    {float_format}
    {print_input}

    """

    tsd = tsutils.common_kwds(
        tsutils.read_iso_ts(input_ts),
        start_date=start_date,
        end_date=end_date,
        pick=None,
    )

    lrad = latitude * pd.np.pi / 180.0

    ad = 0.40928 * pd.np.cos(0.0172141 * (172 - tsd.index.dayofyear))
    ss = pd.np.sin(lrad) * pd.np.sin(ad)
    cs = pd.np.cos(lrad) * pd.np.cos(ad)
    x2 = -ss / cs
    delt = 7.6394 * (pd.np.pi / 2.0 - pd.np.arctan(x2 / pd.np.square(1 - x2 ** 2)))
    sunr = 12.0 - delt / 2.0

    # develop hourly distribution given sunrise,
    # sunset and length of day (DELT)
    dtr2 = delt / 2.0
    dtr4 = delt / 4.0
    crad = 2.0 / 3.0 / dtr2 / 60  # using minutes...
    tr2 = sunr + dtr4
    tr3 = tr2 + dtr2
    tr4 = tr3 + dtr4

    sdate = datetime.datetime(tsd.index[0].year, tsd.index[0].month, tsd.index[0].day)
    edate = (
        datetime.datetime(tsd.index[-1].year, tsd.index[-1].month, tsd.index[-1].day)
        + datetime.timedelta(days=1)
        - datetime.timedelta(hours=1)
    )
    datevalue = pd.DatetimeIndex(start=sdate, end=edate, freq="H")
    fdata = pd.DataFrame([pd.np.nan] * (len(datevalue)), index=datevalue)
    fdata[0] = 0.0
    fdata[-1] = 0.0
    for index in range(len(sunr)):
        cdate = tsd.index[index]
        fdata[
            datetime.datetime(cdate.year, cdate.month, cdate.day, int(sunr[index]))
        ] = 0.0
        fdata[
            datetime.datetime(cdate.year, cdate.month, cdate.day, int(tr4[index]))
        ] = 0.0
        fdata[
            datetime.datetime(cdate.year, cdate.month, cdate.day, int(tr2[index]))
        ] = 1.0
        fdata[
            datetime.datetime(cdate.year, cdate.month, cdate.day, int(tr3[index]))
        ] = 1.0
    fdata = fdata.interpolate("linear")

    fdata = fdata.fillna(0.0)

    ndf = pd.merge(
        pd.DataFrame(crad, index=tsd.index),
        fdata,
        left_index=True,
        right_index=True,
        how="outer",
    )
    ndf.ffill(inplace=True)
    return tsutils.print_input(print_input, tsd, fdata, None, float_format=float_format)


def main():
    """ Main """
    if not os.path.exists("debug_mettoolbox"):
        sys.tracebacklimit = 0
    mando.main()


if __name__ == "__main__":
    main()
