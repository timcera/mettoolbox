import datetime
import warnings
from contextlib import suppress
from typing import Optional, Union

import numpy as np
import pandas as pd
from pydantic import PositiveInt, confloat, validate_arguments
from toolbox_utils import tsutils
from tstoolbox import tstoolbox
from typing_extensions import Literal

from . import tdew as tdew_melo
from .melodist.melodist.humidity import (
    calculate_month_hour_precip_mean,
    disaggregate_humidity,
)
from .melodist.melodist.radiation import disaggregate_radiation
from .melodist.melodist.temperature import disaggregate_temperature, get_shift_by_data
from .melodist.melodist.util.util import (
    calculate_mean_daily_course_by_month,
    get_sun_times,
)
from .melodist.melodist.wind import disaggregate_wind


@tsutils.transform_args(source_units=tsutils.make_list, target_units=tsutils.make_list)
@validate_arguments
def single_target_units(source_units, target_units, default=None, cnt=1):
    if default is None:
        return source_units

    if target_units is None:
        return [default] * len(source_units)

    tunits = set(target_units)
    if len(tunits) != cnt:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                Since creating a single disaggregated time-series there can
                only be a single "target_units".  You gave "{target_units}".
                """
            )
        )
    if len(source_units) == len(target_units):
        return target_units

    return [target_units[0]] * len(source_units)


@validate_arguments(config=dict(arbitrary_types_allowed=True))
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
    temp_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_mean_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    lat: Optional[confloat(ge=-90, le=90)] = None,
    lon: Optional[confloat(ge=-180, le=180)] = None,
    hourly: Optional[Union[str, pd.Series]] = None,
):
    """Disaggregate daily temperature to hourly temperature."""
    target_units = single_target_units(source_units, target_units, "degC")

    pd.options.display.width = 60

    if (
        method in ("mean_course_min_max", "mean_course_mean")
        or min_max_time == "sun_loc_shift"
        or max_delta
    ) and hourly is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
                The methods "mean_course_min", "mean_course_mean", or if
                `max_delta` is True, or if `min_max_time` is "sun_loc_shift"
                require a HOURLY temperature values in the CSV file specified
                by the keyword `hourly`.
                """
            )
        )

    if (
        method in ("mean_course_min_max", "mean_course_mean")
        or min_max_time == "sun_loc_shift"
        or max_delta
    ):
        hourly = tstoolbox.read(hourly)
        mean_course = calculate_mean_daily_course_by_month(
            hourly.squeeze(), normalize=True
        )

        if min_max_time == "sun_loc_shift" or max_delta:
            max_delta = get_shift_by_data(hourly.squeeze(), lon, lat, round(lon / 15.0))
        else:
            max_delta = None
    else:
        mean_course = None

    if temp_min_col is None or temp_max_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                For "temperature" disaggregation you need to supply the daily
                minimum column (name or number, data column numbering starts at
                1) and the daily maximum column (name or number).

                Instead `temp_min_col` is {temp_min_col} and `temp_max_col` is
                {temp_max_col}
                """
            )
        )

    with suppress(TypeError):
        temp_min_col = int(temp_min_col)
    with suppress(TypeError):
        temp_max_col = int(temp_max_col)

    columns = [temp_min_col, temp_max_col]
    if temp_mean_col is not None:
        with suppress(TypeError):
            temp_mean_col = int(temp_mean_col)
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
        tsd.columns = ("tmin", "tmax", "temp")
    else:
        tsd.columns = ("tmin", "tmax")

    if any((tsd.tmax <= tsd.tmin).dropna()):
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                On the following dates:

                {tsd[tsd.tmax <= tsd.tmin].index},

                minimum temperature values in column "{temp_min_col}" are
                greater than or equal to the maximum temperature values in
                column "{temp_max_col}".
                """
            )
        )

    if temp_mean_col is None:
        warnings.warn(
            tsutils.error_wrapper(
                """
                Since `temp_mean_col` is None, the average daily temperature
                will be estimated by the average of `temp_min_col` and
                `temp_max_col`
                """
            )
        )
        tsd["temp"] = (tsd.tmin + tsd.tmax) / 2.0

        if any((tsd.tmin >= tsd.temp).dropna()) or any((tsd.tmax <= tsd.temp).dropna()):
            raise ValueError(
                tsutils.error_wrapper(
                    f"""
                    On the following dates:

                    {tsd[tsd.tmin >= tsd.temp | tsd.tmax <= tsd.temp]},

                    the daily average is either below or equal to the minimum
                    temperature in column {temp_min_col} or higher or equal to
                    the maximum temperature in column {temp_max_col}.
                    """
                )
            )

    if min_max_time == "fix":
        # Not dependent on sun, just average values.
        sun_times = pd.DataFrame(
            index=[1], columns=("sunrise", "sunnoon", "sunset", "daylength")
        )
        sun_times.sunrise = 7
        sun_times.sunnoon = 12
        sun_times.sunset = 19
        sun_times.daylength = 12
    elif lat is None or lon is None:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                The `min_max_time` options other than "fix" require calculation
                of sunrise, sun noon, sunset, and day length.  The calculation
                requires the latitude with keyword "lat" and longitude with
                keyword "lon".

                You gave:

                lat={lat}

                lon={lon}
                """
            )
        )

    else:
        sun_times = get_sun_times(tsd.index, float(lon), float(lat), round(lon / 15.0))

    ntsd = pd.DataFrame(
        disaggregate_temperature(
            tsd,
            method=method,
            min_max_time=min_max_time,
            mod_nighttime=mod_nighttime,
            max_delta=max_delta,
            mean_course=mean_course,
            sun_times=sun_times,
        )
    )

    ntsd.columns = [f"temperature:{target_units[0]}:disagg"]

    return tsutils.return_input(print_input, tsd, ntsd)


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def prepare_hum_tdew(
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
    hum_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    hum_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    hum_mean_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    precip_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    a0=None,
    a1=None,
    kr=None,
    hourly_temp=None,
    hourly_precip_hum=None,
    preserve_daily_mean=None,
    disagg_type=None,
):
    """Disaggregate daily humidity to hourly humidity data."""
    target_units = single_target_units(source_units, target_units, "")

    if method == "equal" and hum_mean_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
                If `method` is "equal" then the mean daily humidity is
                a required column identified with the keyword `hum_mean_col`
                """
            )
        )

    if method == "month_hour_precip_mean" and precip_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
                If `method` is "month_hour_precip_mean" then the daily precip
                is a required column identified with the keyword
                `precip_col`
                """
            )
        )

    if (
        method in ("minimal", "dewpoint_regression", "linear_dewpoint_variation")
        and temp_min_col is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
                If `method` is "minimal", "dewpoint_regression", or
                "linear_dewpoint_variation" then the minimum daily temperature
                is a required column identified with the keyword
                `temp_min_col`.
                """
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
                f"""
                If `method` is "min_max" then:

                Minimum daily humidity is a required column identified with the
                keyword `hum_min_col`.  You gave {hum_min_col}.

                Maximum daily humidity is a required column identified with the
                keyword `hum_max_col`.  You gave {hum_max_col}.

                Minimum daily temperature is a required column identified with
                the keyword `temp_min_col`.  You gave {temp_min_col}.

                Maximum daily temperature is a required column identified with
                the keyword `temp_max_col`.  You gave {temp_max_col}.
                """
            )
        )

    if method in ("dewpoint_regression", "linear_dewpoint_variation") and (
        a0 is None or a1 is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
                If `method` is "dewpoint_regression" or
                "linear_dewpoint_variation" then a0 and a1 must be given.
                """
            )
        )

    if method == "linear_dewpoint_variation" and kr is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
                If `method` is "linear_dewpoint_variation" then kr must be
                given
                """
            )
        )

    if (
        method
        in (
            "minimal",
            "dewpoint_regression",
            "linear_dewpoint_variation",
            "min_max",
        )
        and hourly_temp is None
    ):
        raise ValueError(
            tsutils.error_wrapper(
                """
                If `method` is "minimal", "dewpoint_regression",
                "linear_dewpoint_variation", or "min_max" then hourly
                temperature is required identified by the filename in keyword
                `hourly_temp`.
                """
            )
        )

    pd.options.display.width = 60

    columns = []
    if method == "equal":
        with suppress(TypeError):
            hum_mean_col = int(hum_mean_col)
        columns.append(hum_mean_col)

    if method == "min_max":
        with suppress(TypeError):
            temp_min_col = int(temp_min_col)
        columns.append(temp_min_col)
        with suppress(TypeError):
            temp_max_col = int(temp_max_col)
        columns.append(temp_max_col)
        with suppress(TypeError):
            hum_min_col = int(hum_min_col)
        columns.append(hum_min_col)
        with suppress(TypeError):
            hum_max_col = int(hum_max_col)
        columns.append(hum_max_col)

    if method in ("minimal", "dewpoint_regression", "linear_dewpoint_variation"):
        with suppress(TypeError):
            temp_min_col = int(temp_min_col)
        columns.append(temp_min_col)

    if method == "month_hour_precip_mean":
        with suppress(TypeError):
            precip_col = int(precip_col)
        columns.append(precip_col)

    if preserve_daily_mean is not None and method in (
        "minimal",
        "dewpoint_regression",
        "linear_dewpoint_variation",
        "min_max",
        "month_hour_precip_mean",
    ):
        with suppress(TypeError):
            hum_mean_col = int(preserve_daily_mean)
        columns.append(hum_mean_col)

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
        tsd.columns = ["hum"]

    if preserve_daily_mean is not None:
        if method in ("minimal", "dewpoint_regression", "linear_dewpoint_variation"):
            tsd.columns = ("tmin", "hum")
        if method == "min_max":
            tsd.columns = ("tmin", "tmax", "hum_min", "hum_max", "hum")
        elif method == "month_hour_precip_mean":
            tsd.columns = ("precip", "hum")
        preserve_daily_mean = True
    else:
        if method in ("minimal", "dewpoint_regression", "linear_dewpoint_variation"):
            tsd.columns = "tmin"
        if method == "min_max":
            tsd.columns = ("tmin", "tmax", "hum_min", "hum_max")

        elif method == "month_hour_precip_mean":
            tsd.columns = ["precip"]
    if disagg_type == "humidity":
        if method in [
            "minimal",
            "dewpoint_regression",
            "linear_dewpoint_variation",
            "min_max",
        ]:
            hourly_temp = tstoolbox.read(hourly_temp)
            hourly_temp = hourly_temp.astype(float).squeeze()
    elif disagg_type == "dewpoint":
        if method in [
            "equal",
            "minimal",
            "dewpoint_regression",
            "linear_dewpoint_variation",
            "min_max",
            "month_hour_precip_mean",
        ]:
            hourly_temp = tstoolbox.read(hourly_temp)
            hourly_temp = hourly_temp.astype(float).squeeze()

    if method == "month_hour_precip_mean":
        hourly_precip_hum = tstoolbox.read(hourly_precip_hum)
        month_hour_precip_mean = calculate_month_hour_precip_mean(hourly_precip_hum)
    else:
        month_hour_precip_mean = "None"

    return tsd, hourly_temp, month_hour_precip_mean


@validate_arguments(config=dict(arbitrary_types_allowed=True))
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
    hum_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    hum_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    hum_mean_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    precip_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    a0=None,
    a1=None,
    kr=None,
    hourly_temp=None,
    hourly_precip_hum=None,
    preserve_daily_mean=None,
):
    """Disaggregate daily humidity to hourly humidity data."""
    target_units = single_target_units(source_units, target_units, "")

    tsd, hourly_temp, month_hour_precip_mean = prepare_hum_tdew(
        method,
        source_units,
        input_ts=input_ts,
        columns=columns,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        index_type=index_type,
        names=names,
        target_units=target_units,
        hum_min_col=hum_min_col,
        hum_max_col=hum_max_col,
        hum_mean_col=hum_mean_col,
        temp_min_col=temp_min_col,
        temp_max_col=temp_max_col,
        precip_col=precip_col,
        a0=a0,
        a1=a1,
        kr=kr,
        hourly_temp=hourly_temp,
        hourly_precip_hum=hourly_precip_hum,
        preserve_daily_mean=preserve_daily_mean,
        disagg_type="humidity",
    )

    ntsd = pd.DataFrame(
        disaggregate_humidity(
            tsd.astype(float),
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


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def dewpoint_temperature(
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
    hum_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    hum_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    hum_mean_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    precip_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    a0=None,
    a1=None,
    kr=None,
    hourly_temp=None,
    hourly_precip_hum=None,
    preserve_daily_mean=None,
):
    """Disaggregate daily humidity to hourly humidity data."""
    # target_units = single_target_units(source_units, target_units, "")
    target_units = single_target_units(source_units, target_units, "degK")

    tsd, hourly_temp, month_hour_precip_mean = prepare_hum_tdew(
        method,
        source_units,
        input_ts=input_ts,
        columns=columns,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        index_type=index_type,
        names=names,
        target_units=target_units,
        hum_min_col=hum_min_col,
        hum_max_col=hum_max_col,
        hum_mean_col=hum_mean_col,
        temp_min_col=temp_min_col,
        temp_max_col=temp_max_col,
        precip_col=precip_col,
        a0=a0,
        a1=a1,
        kr=kr,
        hourly_temp=hourly_temp,
        hourly_precip_hum=hourly_precip_hum,
        preserve_daily_mean=preserve_daily_mean,
        disagg_type="dewpoint",
    )

    ntsd = pd.DataFrame(
        tdew_melo.disaggregate_tdew(
            tsd.astype(float),
            method=method,
            temp=hourly_temp,
            a0=a0,
            a1=a1,
            kr=kr,
            preserve_daily_mean=preserve_daily_mean,
            month_hour_precip_mean=month_hour_precip_mean,
        )
    )

    ntsd.columns = ["dewpoint_temp:degK:disagg"]
    ntsd = tsutils._normalize_units(
        ntsd, source_units="degK", target_units=target_units[0]
    )
    return tsutils.return_input(print_input, tsd, ntsd)


@validate_arguments(config=dict(arbitrary_types_allowed=True))
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
    """Disaggregate daily to hourly data."""
    target_units = single_target_units(source_units, target_units, "m/s")

    if method == "cosine" and (a is None or b is None or t_shift is None):
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                For the "cosine" method, requires the `a`, `b`, and `t_shift`
                keywords.  You gave:

                a = {a}

                b = {b}

                t_shift = {t_shift}
                """
            )
        )
    if method in ("equal", "random") and not (
        a is None or b is None or t_shift is None
    ):
        warnings.warn(
            tsutils.error_wrapper(
                """
                The a, b, and t_shift options are ignored for the "equal" and
                "random" methods.
                """
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

    ndf = pd.DataFrame()
    for _, column_data in tsd.iteritems():
        df = disaggregate_wind(column_data, method=method, a=a, b=b, t_shift=t_shift)
        ndf = ndf.join(df, how="outer")

    return tsutils.return_input(
        print_input,
        tsd,
        ndf,
    )


@validate_arguments(config=dict(arbitrary_types_allowed=True))
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
    glob_swr_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_min_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    temp_max_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
    ssd_col: Optional[Union[PositiveInt, str, pd.Series]] = None,
):
    """Disaggregate daily to hourly data."""
    target_units = single_target_units(source_units, target_units, "W/m**2")

    # target_units = target_units[0] * len(source_units)

    pd.options.display.width = 60

    if method == "mean_course" and hourly_rad is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
                If method is "mean_course" need to supply CSV filename of
                hourly radiation by the `hourly_rad` keyword."""
            )
        )

    if method in ("pot_rad", "mean_course") and glob_swr_col is None:
        raise ValueError(
            tsutils.error_wrapper(
                """
                If method is "pot_rad" or "mean_course" need to supply the
                daily global short wave radiation as column name or index with
                keyword `glob_swr_col`
                """
            )
        )

    if method == "pot_rad_via_bc" and (bristcamp_a is None or bristcamp_c is None):
        raise ValueError(
            tsutils.error_wrapper(
                """
                If method is "pot_rad_via_bc" need to supply the keywords
                `bristcamp_a` and `bristcamp_c`.
                """
            )
        )

    columns = []
    if method in ["pot_rad", "mean_course"]:
        try:
            glob_swr_col = int(glob_swr_col)
        except TypeError:
            pass
        columns.append(glob_swr_col)

    if method in ["pot_rad_via_ssd"]:
        try:
            glob_swr_col = int(ssd_col)
        except TypeError:
            pass
        columns.append(ssd_col)

    if method == "pot_rad_via_bc":
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
        tsd.columns = ["glob"]
    if method in ["pot_rad_via_bc"]:
        tsd.columns = ["tmin", "tmax"]
    if method in ["pot_rad_via_ssd"]:
        tsd.columns = ["ssd"]

    if method == "mean_course":
        hourly_rad = tstoolbox.read(hourly_rad)
        hourly_rad = hourly_rad.astype(float).squeeze()
        mean_course = calculate_mean_daily_course_by_month(
            hourly_rad.squeeze(), normalize=True
        )
        pot_rad = None
    else:
        pot_rad = tstoolbox.read(pot_rad)
        pot_rad = pot_rad.astype(float).squeeze()
        mean_course = None

    sun_times = None
    if method == "pot_rad_via_ssd":
        sun_times = get_sun_times(tsd.index, float(lon), float(lat), round(lon / 15.0))

    ntsd = pd.DataFrame(
        disaggregate_radiation(
            tsd.astype(float),
            method=method,
            sun_times=sun_times,
            pot_rad=pot_rad,
            angstr_a=angstr_a,
            angstr_b=angstr_b,
            bristcamp_a=bristcamp_a,
            bristcamp_c=bristcamp_c,
            mean_course=mean_course,
        )
    )
    ntsd.columns = ["Radiation:W/m**2:disagg"]
    return tsutils.return_input(print_input, tsd, ntsd)


@validate_arguments(config=dict(arbitrary_types_allowed=True))
def precipitation(
    method: Literal["equal", "cascade", "masterstation"],
    source_units,
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
    columns=None,
    masterstation_hour_col: Optional[Union[PositiveInt, str]] = None,
):
    """Disaggregate daily to hourly data."""
    target_units = single_target_units(source_units, target_units, "mm")

    pd.options.display.width = 60

    tsd = tsutils.common_kwds(
        input_tsd=tsutils.make_list(input_ts),
        skiprows=skiprows,
        index_type=index_type,
        start_date=start_date,
        end_date=end_date,
        round_index=round_index,
        names=names,
        dropna=dropna,
        clean=clean,
        source_units=source_units,
        target_units=target_units,
        usecols=columns,
    )

    if method == "masterstation":
        try:
            # If masterstations_hour_col is a column name:
            masterstation_hour_col = tsd.columns.get_loc(masterstation_hour_col)
        except KeyError:
            # If masterstations_hour_col is a column number:
            masterstation_hour_col = int(masterstation_hour_col) - 1

        try:
            mhour = tsd[masterstation_hour_col].to_frame()
        except:
            mhour = tsutils.common_kwds(
                input_tsd=tsutils.make_list(input_ts),
                skiprows=skiprows,
                index_type=index_type,
                start_date=start_date,
                end_date=end_date,
                round_index=round_index,
                names=names,
                dropna=dropna,
                clean=clean,
                source_units=source_units,
                target_units=target_units,
                usecols=columns,
            )

        # Should only be one hourly column in the input.
        dsum = mhour.groupby(pd.Grouper(freq="D")).sum().asfreq("H", method="ffill")
        master = mhour.join(dsum, rsuffix="sum")
        mask = master.iloc[:, 0] > 0.0
        master = (
            master.loc[mask, master.columns[0]] / master.loc[mask, master.columns[1]]
        ).to_frame()
        ntsd = tsd.loc[:, tsd.columns != masterstation_hour_col].asfreq(
            "H", method="ffill"
        )
        ntsd = ntsd.join(master)
        ntsd = ntsd.loc[:, tsd.columns != masterstation_hour_col].multiply(
            ntsd.iloc[:, -1:], axis="index"
        )
        # All the remaining columns are daily.
        ntsd = (
            tsd.loc[:, tsd.columns != masterstation_hour_col]
            .asfreq("H", method="ffill")
            .mul(master, axis="rows")
        )

    return tsutils.return_input(print_input, tsd, ntsd)


@validate_arguments(config=dict(arbitrary_types_allowed=True))
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
    lat: Optional[confloat(ge=-90, le=90)] = None,
):
    """Disaggregate daily to hourly data."""
    target_units = single_target_units(source_units, target_units)

    pd.options.display.width = 60

    if method == "trap" and lat is None:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                The "trap" method requires latitude with the `lat` keyword.
                You gave "{lat}".
                """
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
        delt = 7.6394 * (np.pi / 2.0 - np.arctan(x2 / np.square(1 - x2**2)))
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
            fdata.loc[
                datetime.datetime(cdate.year, cdate.month, cdate.day, int(sunr[index])),
                :,
            ] = 0.0
            fdata.loc[
                datetime.datetime(
                    cdate.year, cdate.month, cdate.day, int(tr4[index]) + 1
                ),
                :,
            ] = 0.0
            fdata.loc[
                datetime.datetime(
                    cdate.year, cdate.month, cdate.day, int(round(tr2[index]))
                ),
                :,
            ] = 1.0
            fdata.loc[
                datetime.datetime(
                    cdate.year, cdate.month, cdate.day, int(round(tr3[index]))
                ),
                :,
            ] = 1.0

        fdata.iloc[0, :] = 0.0
        fdata.iloc[-1, :] = 0.0

        fdata = fdata.interpolate("linear")

        fdata = fdata.fillna(0.0)

        fdata = fdata / fdata.groupby(pd.Grouper(freq="D")).sum().resample("H").ffill()

        fdata = fdata * ndata

        fdata = fdata.iloc[:-1, :]

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

        fdata = fdata.iloc[:-1, :]

    return tsutils.print_input(print_input, tsd, fdata, None)
