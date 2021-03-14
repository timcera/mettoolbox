#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from typing import Optional, Union

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import warnings
import datetime

import numpy as np
import pandas as pd
import typic

from tstoolbox import tsutils
from tstoolbox import tstoolbox

from .melodist.melodist.util.util import get_sun_times
from .melodist.melodist.temperature import disaggregate_temperature
from .melodist.melodist.temperature import get_shift_by_data
from .melodist.melodist.humidity import calculate_month_hour_precip_mean
from .melodist.melodist.humidity import disaggregate_humidity
from .melodist.melodist.wind import disaggregate_wind
from .melodist.melodist.radiation import disaggregate_radiation
from .melodist.melodist.precipitation import disagg_prec

warnings.filterwarnings("ignore")


def single_target_units(source_units, target_units, default=None):
    if default is None:
        return source_units

    if target_units is None:
        return [default] * len(source_units)

    tunits = set(target_units)
    if len(tunits) != 1:
        raise ValueError(
            tsutils.error_wrapper(
                """
Since creating a single disaggregated time-series there can only be
a single "target_units".  You gave "{target_units}".
""".format(
                    **locals()
                )
            )
        )
    return target_units[0] * len(source_units)


@typic.constrained(ge=-90, le=90)
class FloatLatitude(float):
    """ -90 <= float <= 90 """


@typic.constrained(ge=-180, le=180)
class FloatLongitude(float):
    """ -180 <= float <= 180 """


@typic.al
def temperature(
    method: Literal[
        "sine_min_max", "sine_mean", "sine", "mean_course_min_max", "mean_course_mean"
    ],
    source_units,
    min_max_time: Literal["fix", "sun_loc", "sun_loc_shift"] = "fix",
    mod_nighttime: bool = False,
    input_ts="-",
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
    names=None,
    print_input=False,
    target_units=None,
    max_delta: bool = False,
    temp_min_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    temp_max_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    temp_mean_col: Optional[Union[tsutils.IntGreaterEqualToOne, str]] = None,
    lat: Optional[FloatLatitude] = None,
    lon: Optional[FloatLongitude] = None,
    hourly: Optional[str] = None,
):
    """Disaggregate daily to hourly data.

    disaggregate_temperature(data_daily,
                             method='sine_min_max',
                             min_max_time='fix',
                             mod_nighttime=False,
                             max_delta=None,
                             mean_course=None,
                             sun_times=None):

    data_daily :      daily data
    method :          method to disaggregate
    min_max_time:     "fix" - min/max temperature at fixed times 7h/14h,
                      "sun_loc" - min/max calculated by sunrise/sunnoon + 2h,
                      "sun_loc_shift" - min/max calculated by sunrise/sunnoon +
                                        monthly mean shift,
    mod_nighttime:    ?
    max_delta:        maximum monthly temperature shift as returned by
                      get_shift_by_data()
    mean_course:      ?
    sun_times:        times of sunrise/noon as returned by get_sun_times()

    if method in ('sine_min_max', 'sine_mean', 'sine')
        .tmin from temp_min_col
        .tmax from temp_max_col
        .temp from temp_mean_col

    if method in ('mean_course_min', 'mean_course_mean')
        .tmin from temp_min_col
        .tmax from temp_max_col
        require hourly temperature perhaps from nearby station in 'mean_course'

    if method == 'mean_course_mean'
        .temp from temp_mean_col

    sun_times = get_sun_times(dates, lon, lat, round(lon/15.0))

    max_delta = get_shift_by_data(temp_hourly, lon, lat, round(lon/15.0))
    """
    source_units = tsutils.make_list(source_units)
    target_units = tsutils.make_list(target_units)

    target_units = single_target_units(source_units, target_units, "degC")

    pd.options.display.width = 60

    if (
        method in ["mean_course_min", "mean_course_mean"] or max_delta is True
    ) and hourly is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
The methods "mean_course_min", "mean_course_mean", or if `max_delta` is
True, require a HOURLY temperature values in the CSV file specified by the
keyword `hourly`."""
            )
        )

    if method in ["mean_course_min", "mean_course_mean"] or max_delta is True:
        hourly = tstoolbox.read(hourly)

    if max_delta is True:
        max_delta = get_shift_by_data(hourly, lon, lat, round(lon / 15.0))
    else:
        max_delta = None

    if temp_min_col is None or temp_max_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
For "temperature" disaggregation you need to supply the daily minimum
column (name or number, data column numbering starts at 1) and the daily
maximum column (name or number).

Instead `temp_min_col` is {temp_min_col} and `temp_max_col` is
{temp_max_col}""".format(
                    **locals()
                )
            )
        )

    columns = []
    try:
        temp_min_col = int(temp_min_col)
    except TypeError:
        pass
    columns.append(temp_min_col)

    try:
        temp_max_col = int(temp_max_col)
    except TypeError:
        pass
    columns.append(temp_max_col)

    if temp_mean_col is not None:
        try:
            temp_mean_col = int(temp_mean_col)
        except TypeError:
            pass
        columns.append(temp_mean_col)

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

    if len(tsd.columns) == 3:
        tsd.columns = ["tmin", "tmax", "temp"]
    else:
        tsd.columns = ["tmin", "tmax"]

    if any(tsd.tmax <= tsd.tmin):
        raise ValueError(
            tsutils.error_wrapper(
                """
On the following dates:

{0},

minimum temperature values in column "{1}" are greater than or equal to
the maximum temperature values in column "{2}".""".format(
                    tsd[tsd.tmax <= tsd.tmin].index, temp_min_col, temp_max_col
                )
            )
        )

    if temp_mean_col is None:
        warnings.warn(
            tsutils.error_wrapper(
                """
Since `temp_mean_col` is None, the average daily temperature will be
estimated by the average of `temp_min_col` and `temp_max_col`""".format(
                    **locals()
                )
            )
        )
        tsd.temp = (tsd.tmin + tsd.tmax) / 2.0

        if any(tsd.tmin >= tsd.temp) or any(tsd.tmax <= tsd.temp):
            raise ValueError(
                tsutils.error_wrapper(
                    """
On the following dates:

{0},

the daily average is either below or equal to the minimum temperature in column {1}
or higher or equal to the maximum temperature in column {2}.""".format(
                        tsd[tsd.tmin >= tsd.temp | tsd.tmax <= tsd.temp],
                        temp_min_col,
                        temp_max_col,
                    )
                )
            )

    if min_max_time == "fix":
        # Not dependent on sun, just average values.
        sun_times = pd.DataFrame(
            index=[1], columns=["sunrise", "sunnoon", "sunset", "daylength"]
        )
        sun_times.sunrise = 7
        sun_times.sunnoon = 12
        sun_times.sunset = 19
        sun_times.daylength = 12
    else:
        if lat is None or lon is None:
            raise ValueError(
                tsutils.error_wrapper(
                    """
The `min_max_time` options other than "fix" require calculation of
sunrise, sun noon, sunset, and day length.  The calculation requires the
latitude with keyword "lat" and longitude with keyword "lon".
You gave:

    lat={lat}

    lon={lon}
""".format(
                        **locals()
                    )
                )
            )

        sun_times = get_sun_times(tsd.index, float(lon), float(lat), round(lon / 15.0))

    ntsd = pd.DataFrame(
        disaggregate_temperature(
            tsd,
            method=method,
            min_max_time=min_max_time,
            mod_nighttime=mod_nighttime,
            max_delta=max_delta,
            mean_course=hourly,
            sun_times=sun_times,
        )
    )

    ntsd.columns = ["temperature:{0}:disagg".format(target_units[0])]

    return tsutils.return_input(print_input, tsd, ntsd)


@typic.al
def humidity(
    method: Literal[
        "equal",
        "minimal",
        "dewpoint_regression",
        "linear_dewpoint_variation",
        "min_max",
        "month_hour_precip_mean",
    ],
    source_units,
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
    target_units=None,
    print_input=False,
    hum_min_col=None,
    hum_max_col=None,
    hum_mean_col=None,
    temp_min_col=None,
    temp_max_col=None,
    a0=None,
    a1=None,
    kr=None,
    hourly_temp=None,
    preserve_daily_mean=None,
):
    """Disaggregate daily humidity to hourly humidity data.

    disaggregate_humidity(data_daily, method='equal', temp=None,
                          a0=None, a1=None, kr=None,
                          month_hour_precip_mean=None, preserve_daily_mean=False):
    Args:
        daily_data: daily values
        method: keyword specifying the disaggregation method to be used
        temp: hourly temperature time series (necessary for some methods)
        kr: parameter for linear_dewpoint_variation method (6 or 12)
        month_hour_precip_mean: [month, hour, precip(y/n)] categorical mean values
        preserve_daily_mean: if True, correct the daily mean values of the disaggregated
            data with the observed daily means.


    if method=equal
        .hum from hum_mean_col
    if method in ["minimal", "dewpoint_regression", "linear_dewpoint_variation"]
        .tmin from temp_min_col
    if method=min_max need
        .hum_min from hum_min_col
        .hum_max from hum_max_col
        .tmin from temp_min_col
        .tmax from temp_max_col

    if method in ["dewpoint_regression", "linear_dewpoint_variation"]
        a0
        a1
    if method in ["linear_dewpoint_variation"]
        kr

    if preserve_daily_mean is True
        .hum from hum_mean_col

    if method in ["minimal",
                  "dewpoint_regression",
                  "linear_dewpoint_variation",
                  "min_max"]
        need HOURLY temperature in 'temp'
    """
    source_units = tsutils.make_list(source_units)
    target_units = tsutils.make_list(target_units)

    target_units = single_target_units(source_units, target_units, "")

    if method == "equal" and hum_mean_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
If `method` is "equal" then the mean daily humidity is a required column
identified with the keyword `hum_mean_col`"""
            )
        )

    if (
        method in ["minimal", "dewpoint_regression", "linear_dewpoint_variation"]
        and temp_min_col is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
If `method` is "minimal", "dewpoint_regression", or
"linear_dewpoint_variation" then the minimum daily temperature is a required
column identified with the keyword `temp_min_col`."""
            )
        )

    if method == "min_max" and (
        hum_min_col is None
        or hum_max_col is None
        or temp_min_col is None
        or temp_max_col is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
If `method` is "min_max" then:

Minimum daily humidity is a required column identified with the keyword
`hum_min_col`.  You gave {hum_min_col}.

Maximum daily humidity is a required column identified with the keyword
`hum_max_col`.  You gave {hum_max_col}.

Minimum daily temperature is a required column identified with the
keyword `temp_min_col`.  You gave {temp_min_col}.

Maximum daily temperature is a required column identified with the
keyword `temp_max_col`.  You gave {temp_max_col}.
""".format(
                    **locals()
                )
            )
        )

    if method in ["dewpoint_regression", "linear_dewpoint_variation"] and (
        a0 is None or a1 is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
If `method` is "dewpoint_regression" or "linear_dewpoint_variation" then
a0 and a1 must be given."""
            )
        )

    if method == "linear_dewpoint_variation" and kr is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
If `method` is "linear_dewpoint_variation" then kr must be given"""
            )
        )

    if (
        method
        in [
            "minimal",
            "dewpoint_regression",
            "linear_dewpoint_variation",
            "min_max",
            "month_hour_precip_mean",
        ]
        and hourly_temp is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
If `method` is "minimal", "dewpoint_regression",
"linear_dewpoint_variation", or "min_max" then hourly temperature is
required identified by the filename in keyword `hourly_temp`."""
            )
        )

    pd.options.display.width = 60

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

    if method == "equal":
        tsd["hum"] = tsd["hum_mean_col"]

    if method in ["minimal", "dewpoint_regression", "linear_dewpoint_variation"]:
        tsd["tmin"] = tsd["temp_min_col"]

    if method == "min_max":
        tsd["hum_min"] = tsd["hum_min_col"]
        tsd["hum_max"] = tsd["hum_max_col"]
        tsd["tmin"] = tsd["temp_min_col"]
        tsd["tmax"] = tsd["temp_max_col"]

    if preserve_daily_mean is not None:
        tsd["hum"] = tsd[preserve_daily_mean]
        preserve_daily_mean = True

    if method in [
        "minimal",
        "dewpoint_regression",
        "linear_dewpoint_variation",
        "min_max",
        "month_hour_precip_mean",
    ]:
        hourly_temp = tstoolbox.read(hourly_temp)

    if method == "month_hour_precip_mean":
        month_hour_precip_mean = calculate_month_hour_precip_mean(hourly_temp)

    ntsd = pd.DataFrame(
        disaggregate_humidity(
            tsd,
            method=method,
            temp=hourly_temp,
            a0=a0,
            a1=a1,
            kr=kr,
            preserve_daily_mean=preserve_daily_mean,
            month_hour_precip_mean=month_hour_precip_mean,
        )
    )

    ntsd.columns = ["humidity:{0}:disagg"]

    return tsutils.return_input(print_input, tsd, ntsd)


@typic.al
def wind_speed(
    method: Literal["equal", "cosine", "random"],
    source_units,
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
    target_units=None,
    print_input=False,
    a=None,
    b=None,
    t_shift=None,
):
    """Disaggregate daily to hourly data.
    disaggregate_wind(wind_daily,
                      method='equal',
                      a=None,
                      b=None,
                      t_shift=None):

    Args:
        wind_daily: daily values
        method: keyword specifying the disaggregation method to be used
        a: parameter a for the cosine function
        b: parameter b for the cosine function
        t_shift: parameter t_shift for the cosine function
    """
    source_units = tsutils.make_list(source_units)
    target_units = tsutils.make_list(target_units)

    target_units = single_target_units(source_units, target_units, "m/s")

    target_units = target_units[0] * len(source_units)

    pd.options.display.width = 60

    if method == "cosine" and (a is None or b is None or t_shift is None):
        raise ValueError(
            tsutils.error_wrapper(
                """
For the "cosine" method, requires the `a`, `b`, and `t_shift`
keywords.  You gave:

a = {a}

b = {b}

t_shift = {t_shift}
""".format(
                    **locals()
                )
            )
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
        target_units=target_units,
        clean=clean,
    )

    return tsutils.return_input(
        print_input,
        tsd,
        pd.DataFrame(disaggregate_wind(tsd, method=method, a=a, b=b, t_shift=t_shift)),
    )


@typic.al
def radiation(
    method: Literal["pot_rad", "pot_rad_via_ssd", "pot_rad_via_bc", "mean_course"],
    source_units,
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
    target_units=None,
    print_input=False,
    pot_rad=None,
    angstr_a=0.25,
    angstr_b=0.5,
    bristcamp_a=0.75,
    bristcamp_c=2.4,
    hourly_rad=None,
    lat=None,
    lon=None,
    glob_swr_col=None,
):
    """Disaggregate daily to hourly data.

    disaggregate_radiation(data_daily,
                           sun_times=None,
                           pot_rad=None,
                           method='pot_rad',
                           angstr_a=0.25,
                           angstr_b=0.5,
                           bristcamp_a=0.75,
                           bristcamp_c=2.4,
                           mean_course=None):
    Args:
        daily_data: daily values
        sun_times: daily dataframe including results of the util.sun_times function
        pot_rad: hourly dataframe including potential radiation
        method: keyword specifying the disaggregation method to be used
        angstr_a: parameter a of the Angstrom model (intercept)
        angstr_b: parameter b of the Angstrom model (slope)
        bristcamp_a: ?
        bristcamp_c: ?
        mean_course: monthly values of the mean hourly radiation course

    if method == 'mean_course':
        HOURLY radiation in "mean_course"

    if method in ('pot_rad', 'mean_course')
        .glob from glob_swr_col

    if method == 'pot_rad_via_ssd'
        daily sun_times

    if method == 'pot_rad_via_bc'
        bristcamp_a
        bristcamp_c
    """
    source_units = tsutils.make_list(source_units)
    target_units = tsutils.make_list(target_units)

    target_units = single_target_units(source_units, target_units, "W/m2")

    target_units = target_units[0] * len(source_units)

    pd.options.display.width = 60

    if method == "mean_course" and hourly_rad is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
If method is "mean_course" need to supply CSV filename of hourly
radiation by the `hourly_rad` keyword."""
            )
        )

    if method in ["pot_rad", "mean_course"] and glob_swr_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
If method is "pot_rad" or "mean_course" need to supply the daily global
short wave radiation as column name or index with keyword
`glob_swr_col`"""
            )
        )

    if method == "pot_rad_via_bc" and (bristcamp_a is None or bristcamp_c is None):
        raise ValueError(
            tsutils.error_wrapper(
                """
If method is "pot_rad_via_bc" need to supply the keywords `bristcamp_a`
and `bristcamp_c`."""
            )
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
        target_units=target_units,
        clean=clean,
    )

    if method in ["pot_rad", "mean_course"]:
        try:
            glob_swr_col = glob_swr_col - 1
        except ValueError:
            pass
        tsd["glob"] = tsd[glob_swr_col]

    sun_times = None
    if method == "pot_rad_via_ssd":
        sun_times = get_sun_times(tsd.index, float(lon), float(lat), round(lon / 15.0))

    return tsutils.return_input(
        print_input,
        tsd,
        pd.DataFrame(
            disaggregate_radiation(
                tsd,
                sun_times=sun_times,
                pot_rad=pot_rad,
                method=method,
                angstr_a=angstr_a,
                angstr_b=angstr_b,
                bristcamp_a=bristcamp_a,
                bristcamp_c=bristcamp_c,
                mean_course=hourly_rad,
            )
        ),
    )


@typic.al
def precipitation(
    method: Literal["equal", "cascade", "masterstation"],
    source_units,
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
    target_units=None,
    print_input=False,
):
    """Disaggregate daily to hourly data."""
    source_units = tsutils.make_list(source_units)
    target_units = tsutils.make_list(target_units)

    target_units = single_target_units(source_units, target_units, "mm")

    pd.options.display.width = 60

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

    return tsutils.return_input(
        print_input,
        tsd,
        pd.DataFrame(
            disagg_prec(
                tsd,
                method=method,
            )
        ),
    )


@typic.al
def evaporation(
    method: Literal["trap", "fixed"],
    source_units,
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
    target_units=None,
    print_input=False,
    lat: Optional[FloatLatitude] = None,
):
    """Disaggregate daily to hourly data."""
    source_units = tsutils.make_list(source_units)
    target_units = tsutils.make_list(target_units)

    target_units = single_target_units(source_units, target_units)

    pd.options.display.width = 60

    if method == "trap" and lat is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
The "trap" method requires latitude with the `lat` keyword.  You gave
"{lat}". """.format(
                    **locals()
                )
            )
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
        target_units=target_units,
        clean=clean,
    )

    ntsd = tsd.append(
        pd.DataFrame(
            columns=tsd.columns, index=[tsd.index[-1] + datetime.timedelta(days=1)]
        )
    )
    ndata = ntsd.resample("H").ffill()

    fdata = pd.DataFrame(columns=ndata.columns, index=ndata.index, dtype="f")

    if method == "trap":
        lrad = lat * np.pi / 180.0

        ad = 0.40928 * np.cos(0.0172141 * (172 - tsd.index.dayofyear))
        ss = np.sin(lrad) * np.sin(ad)
        cs = np.cos(lrad) * np.cos(ad)
        x2 = -ss / cs
        delt = 7.6394 * (np.pi / 2.0 - np.arctan(x2 / np.square(1 - x2 ** 2)))
        sunr = 12.0 - delt / 2.0

        # develop hourly distribution given sunrise,
        # sunset and length of day (DELT)
        dtr2 = delt / 2.0
        dtr4 = delt / 4.0
        tr2 = sunr + dtr4
        tr3 = tr2 + dtr2
        tr4 = tr3 + dtr4

        for index, toss in enumerate(sunr):
            cdate = ntsd.index[index]
            fdata.ix[
                datetime.datetime(cdate.year, cdate.month, cdate.day, int(sunr[index])),
                :,
            ] = 0.0
            fdata.ix[
                datetime.datetime(
                    cdate.year, cdate.month, cdate.day, int(tr4[index]) + 1
                ),
                :,
            ] = 0.0
            fdata.ix[
                datetime.datetime(
                    cdate.year, cdate.month, cdate.day, int(round(tr2[index]))
                ),
                :,
            ] = 1.0
            fdata.ix[
                datetime.datetime(
                    cdate.year, cdate.month, cdate.day, int(round(tr3[index]))
                ),
                :,
            ] = 1.0

        fdata.ix[0, :] = 0.0
        fdata.ix[-1, :] = 0.0

        fdata = fdata.interpolate("linear")

        fdata = fdata.fillna(0.0)

        fdata = fdata / fdata.groupby(pd.Grouper(freq="D")).sum().resample("H").ffill()

        fdata = fdata * ndata

        fdata = fdata.ix[:-1, :]

    elif method == "fixed":
        # DATA EVAPDIST / 0.000,0.000,0.000,0.000,0.000,0.000,0.019,0.041,
        # $ 0.067,0.088,0.102,0.110,0.110,0.110,0.105,0.095,
        # $ 0.081,0.055,0.017,0.000,0.000,0.000,0.000,0.000
        fdata = fdata.fillna(0.0)

        fdata[fdata.index.hour == 7] = 0.019
        fdata[fdata.index.hour == 8] = 0.041
        fdata[fdata.index.hour == 9] = 0.067
        fdata[fdata.index.hour == 10] = 0.088
        fdata[fdata.index.hour == 11] = 0.102
        fdata[fdata.index.hour == 12] = 0.110
        fdata[fdata.index.hour == 13] = 0.110
        fdata[fdata.index.hour == 14] = 0.110
        fdata[fdata.index.hour == 15] = 0.105
        fdata[fdata.index.hour == 16] = 0.095
        fdata[fdata.index.hour == 17] = 0.081
        fdata[fdata.index.hour == 18] = 0.055
        fdata[fdata.index.hour == 19] = 0.017

        fdata = fdata * ndata

        fdata = fdata.ix[:-1, :]

    return tsutils.print_input(print_input, tsd, fdata, None)
