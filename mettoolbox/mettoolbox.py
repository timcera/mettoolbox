#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os.path
import warnings

from mando.rst_text_formatter import RSTHelpFormatter

from tstoolbox import tsutils

from . import disaggregate
from . import pet

from mando import Program

warnings.filterwarnings("ignore")

program = Program("mettoolbox", "0.0")

program.add_subprog("disaggregate")
program.add_subprog("pet")

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
sunits = _LOCAL_DOCSTRINGS["source_units"]
sunits = sunits.split("\n")
del sunits[1:3]
_LOCAL_DOCSTRINGS["psource_units"] = "\n".join(sunits)


@program.command()
def about():
    """Display version number and system information."""
    tsutils.about(__name__)


@program.disaggregate.command(
    "evaporation", formatter_class=RSTHelpFormatter, doctype="numpy"
)
@tsutils.doc(_LOCAL_DOCSTRINGS)
def evaporation_cli(
    method,
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
    tablefmt="csv",
    lat=None,
):
    """Disaggregate daily evaporation to hourly evaporation.

    Parameters
    ==========
    method: str
        This is the method that will be used to disaggregate the daily
        evaporation data.

        There are two methods, a trapezoidal shape from sunrise to
        sunset called "trap" and a fixed, smooth curve starting at 0700
        (7 am) and stopping at 1900 (7 pm) called "fixed".
    {input_ts}
    {columns}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {psource_units}
    {target_units}
    {print_input}
    {tablefmt}
    lat: float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    """
    tsutils._printiso(
        disaggregate.evaporation(
            method,
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
            source_units=source_units,
            target_units=target_units,
            print_input=print_input,
            lat=lat,
        ),
        tablefmt=tablefmt,
    )


disaggregate.evaporation.__doc__ = evaporation_cli.__doc__


@program.disaggregate.command(
    "humidity", formatter_class=RSTHelpFormatter, doctype="numpy"
)
@tsutils.doc(_LOCAL_DOCSTRINGS)
def humidity_cli(
    method,
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
    tablefmt="csv",
    hum_min_col=None,
    hum_max_col=None,
    hum_mean_col=None,
    a0=None,
    a1=None,
    kr=None,
    hourly_temp=None,
    preserve_daily_mean=None,
):
    """Disaggregate daily relative humidity to hourly humidity.

    Relative humidity disaggregation requires the following input data.

    +--------------+---------------------------------------------+
    | Input data   | Description                                 |
    +==============+=============================================+
    | hum_min_col  | Required column name or number representing |
    |              | the minimum daily relative humidity.        |
    +--------------+---------------------------------------------+
    | hum_max_col  | Required column name or number representing |
    |              | the maximum daily relative humidity.        |
    +--------------+---------------------------------------------+
    | hum_mean_col | Optional column name or number representing |
    |              | the average daily relative humidity.        |
    |              | Default is None and if None will be         |
    |              | calculated as average of `hum_tmin_col` and |
    |              | `hum_tmax_col`.                             |
    +--------------+---------------------------------------------+

    Parameters
    ==========
    method: str

        Available disaggregation methods for
        humidity.

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

        Required keywords for each method.  The "Column Name/Index
        Keywords" represent the column name or index (data columns
        starting numbering at 1) in the input dataset.

        +---------------------------+----------------+---------------+
        | `method`                  | Column Name/   | Other         |
        |                           | Index Keywords | Keywords      |
        +---------------------------+----------------+---------------+
        | equal                     | `hum_mean_col` |               |
        +---------------------------+----------------+---------------+
        | minimal                   | `temp_min_col` | `hourly_temp` |
        +---------------------------+----------------+---------------+
        | dewpoint_regression       | `temp_min_col` | `a0`          |
        |                           |                | `a1`          |
        |                           |                | `hourly_temp` |
        +---------------------------+----------------+---------------+
        | linear_dewpoint_variation | `temp_min_col` | `a0`          |
        |                           |                | `a1`          |
        |                           |                | `kr`          |
        |                           |                | `hourly_temp` |
        +---------------------------+----------------+---------------+
        | min_max                   | `hum_min_col`  | `hourly_temp` |
        |                           | `hum_max_col`  |               |
        |                           | `temp_min_col` |               |
        |                           | `temp_max_col` |               |
        +---------------------------+----------------+---------------+
        | month_hour_precip_mean    | `precip_col`   |               |
        +---------------------------+----------------+---------------+
    {psource_units}
    {input_ts}
    {columns}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {target_units}
    {print_input}
    {tablefmt}
    hum_min_col:
        Column index (data columns start numbering at 1) or column name
        from the input data that contains the daily minimum humidity.
    hum_max_col:
        Column index (data columns start numbering at 1) or column name
        from the input data that contains the daily maximum humidity.
    hum_mean_col:
        Column index (data columns start numbering at 1) or column name
        from the input data that contains the daily maximum humidity.
    a0: float
        The "a0"
        parameter.
    a1: float
        The "a1"
        parameter.
    kr: int
        Parameter for the "linear_dewpoint_variation"
        method.
    hourly_temp: str
        Filename of a CSV file that contains an hourly time series of
        temperatures.
    preserve_daily_mean: str
        Column name or index (data columns start at 1) that identifies
        the observed daily mean humidity.  If not None will correct the
        daily mean values of the disaggregated data with the observed
        daily mean humidity.
    """
    tsutils._printiso(
        disaggregate.humidity(
            method,
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
            source_units=source_units,
            target_units=target_units,
            print_input=print_input,
            hum_min_col=hum_min_col,
            hum_max_col=hum_max_col,
            hum_mean_col=hum_mean_col,
            a0=a0,
            a1=a1,
            kr=kr,
            hourly_temp=hourly_temp,
            preserve_daily_mean=preserve_daily_mean,
        ),
        tablefmt=tablefmt,
    )


disaggregate.humidity.__doc__ = humidity_cli.__doc__


@program.disaggregate.command(
    "precipitation", formatter_class=RSTHelpFormatter, doctype="numpy"
)
@tsutils.doc(_LOCAL_DOCSTRINGS)
def precipitation_cli(
    method,
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
    tablefmt="csv",
):
    """Disaggregate daily precipitation to hourly precipitation.

    Parameters
    ==========
    method: str
        Disaggregation methods available for precipitation.

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

    {input_ts}
    {columns}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {psource_units}
    {target_units}
    {print_input}
    {tablefmt}
    """
    tsutils._printiso(
        disaggregate.precipitation(
            method,
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
            source_units=source_units,
            target_units=target_units,
            print_input=print_input,
        ),
        tablefmt=tablefmt,
    )


disaggregate.precipitation.__doc__ = precipitation_cli.__doc__


@program.disaggregate.command(
    "radiation", formatter_class=RSTHelpFormatter, doctype="numpy"
)
@tsutils.doc(_LOCAL_DOCSTRINGS)
def radiation_cli(
    method,
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
    tablefmt="csv",
    pot_rad=None,
    angstr_a=None,
    angstr_b=None,
    bristcamp_a=None,
    bristcamp_c=None,
    mean_course=None,
    lat=None,
    lon=None,
    hourly_rad=None,
):
    """Disaggregate daily radiation to hourly radiation.

    Parameters
    ==========
    method: str
        Disaggregation methods available for radiation

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

    {input_ts}
    {columns}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {psource_units}
    {target_units}
    {print_input}
    {tablefmt}
    pot_rad: str
        hourly dataframe including potential radiation
    angstr_a: float
        parameter a of the Angstrom model (intercept)
    angstr_b: float
        parameter b of the Angstrom model (slope)
    bristcamp_a: float
        parameter a for bristcamp
    bristcamp_c: float
        parameter c for bristcamp
    hourly_rad: str
        monthly values of the mean hourly radiation course
    lat: float
        Latitude
    lon: float
        Longitude
    mean_course:
        Filename of HOURLY CSV file that contains radiation values to be
        used with the "mean_course" method.
    """
    tsutils._printiso(
        disaggregate.radiation(
            method,
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
            source_units=source_units,
            target_units=target_units,
            print_input=print_input,
            pot_rad=pot_rad,
            angstr_a=angstr_a,
            angstr_b=angstr_b,
            bristcamp_a=bristcamp_a,
            bristcamp_c=bristcamp_c,
            hourly_rad=hourly_rad,
            lat=lat,
            lon=lon,
        ),
        tablefmt=tablefmt,
    )


disaggregate.radiation.__doc__ = radiation_cli.__doc__


@program.disaggregate.command(
    "temperature", formatter_class=RSTHelpFormatter, doctype="numpy"
)
@tsutils.doc(_LOCAL_DOCSTRINGS)
def temperature_cli(
    method,
    source_units,
    min_max_time="fix",
    mod_nighttime=False,
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
    tablefmt="csv",
    temp_min_col=None,
    temp_max_col=None,
    temp_mean_col=None,
    lat=None,
    lon=None,
    hourly=None,
    max_delta=False,
):
    """Disaggregate daily temperature to hourly temperature.

    For straight disaggregation the temperature units are not relevant,
    however other tools in mettoolbox require metric units.  You can use
    `source_units` and `target_units` keywords to change units.

    +---------------+----------------------------+
    | Input Data    | Description                |
    +===============+============================+
    | temp_tmin_col | Required column name or    |
    |               | number representing the    |
    |               | minimum daily temperature. |
    +---------------+----------------------------+
    | temp_tmax_col | Required column name or    |
    |               | number representing the    |
    |               | maximum daily temperature. |
    +---------------+----------------------------+
    | temp_mean_col | Optional column name or    |
    |               | number representing the    |
    |               | average daily temperature. |
    |               | Default is None and if     |
    |               | None will be calculated as |
    |               | average of `temp_tmin_col` |
    |               | and `temp_tmax_col`.       |
    +---------------+----------------------------+

    Parameters
    ==========
    method: str

        Disaggregation methods available for temperature.

        +---------------------+--------------------------------------+
        | `method`            | Description                          |
        +=====================+======================================+
        | sine_min_max        | Standard sine redistribution;        |
        |                     | preserves Tmin and Tmax but not      |
        |                     | Tmean.                               |
        +---------------------+--------------------------------------+
        | sine_mean           | Sine redistribution; preserves       |
        |                     | Tmean and the diurnal temperature    |
        |                     | range (Tmax – Tmin) but not Tmin     |
        |                     | and Tmax.                            |
        +---------------------+--------------------------------------+
        | mean_course_min_max | Redistribute following a prescribed  |
        |                     | temperature course calculated from   |
        |                     | hourly observations; preserves Tmin  |
        |                     | and Tmax.  Hourly CSV filename       |
        |                     | specified with the `hourly` keyword. |
        +---------------------+--------------------------------------+
        | mean_course_mean    | Redistribute following a prescribed  |
        |                     | temperature course calculated from   |
        |                     | hourly observations; preserves       |
        |                     | Tmean and the diurnal temperature    |
        |                     | range. Hourly CSV filename specified |
        |                     | with the `hourly` keyword.           |
        +---------------------+--------------------------------------+
    {psource_units}

    min_max_time: str

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
        Allows one to apply a linear interpolation of night time values,
        which proves preferable during polar nights.

    {input_ts}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {target_units}
    {print_input}
    {tablefmt}
    temp_min_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    temp_mean_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.
    lat: float
        The latitude of the station.  Required if `min_max_time` is
        "sun_loc" or "sun_loc_shift".
    lon: float
        The longitude of the station.  Required if `min_max_time` is
        "sun_loc" or "sun_loc_shift".
    hourly: str
        File name that contains the hourly time series of temperatures
        to use when `method` is "mean_course_min" or "mean_course_mean"
        or when `max_delta` is True.
    max_delta: bool
        Uses maximum delta of hourly values for each month to constrain
        the disaggregated hourly temperature values.  If set to True
        requires an hourly time-series filename specified with the
        `hourly` keyword.
    """
    tsutils._printiso(
        disaggregate.temperature(
            method,
            source_units,
            input_ts=input_ts,
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            skiprows=skiprows,
            index_type=index_type,
            names=names,
            target_units=target_units,
            print_input=print_input,
            min_max_time=min_max_time,
            mod_nighttime=mod_nighttime,
            temp_min_col=temp_min_col,
            temp_max_col=temp_max_col,
            temp_mean_col=temp_mean_col,
            lat=lat,
            lon=lon,
            hourly=hourly,
            max_delta=max_delta,
        ),
        tablefmt=tablefmt,
    )


disaggregate.temperature.__doc__ = temperature_cli.__doc__


@program.disaggregate.command(
    "wind_speed", formatter_class=RSTHelpFormatter, doctype="numpy"
)
@tsutils.doc(_LOCAL_DOCSTRINGS)
def wind_speed_cli(
    method,
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
    tablefmt="csv",
    a=None,
    b=None,
    t_shift=None,
):
    """Disaggregate daily wind speed to hourly wind speed.

    Parameters
    ==========
    method: str
        Disaggregation methods available for wind speed.

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

    {psource_units}
    {input_ts}
    {columns}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {target_units}
    {print_input}
    {tablefmt}
    a: float
        Parameter `a` when method is equal to "cosine".
    b: float
        Parameter `b` when method is equal to "cosine".
    t_shift: float
        Parameter `t_shift` when method is equal to "cosine".
    """
    tsutils._printiso(
        disaggregate.wind_speed(
            method,
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
            source_units=source_units,
            target_units=target_units,
            print_input=print_input,
            a=a,
            b=b,
            t_shift=t_shift,
        ),
        tablefmt=tablefmt,
    )


disaggregate.wind_speed.__doc__ = wind_speed_cli.__doc__


@program.pet.command("hargreaves", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def hargreaves_cli(
    lat,
    temp_min_col=None,
    temp_max_col=None,
    temp_mean_col=None,
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
    tablefmt="csv",
):
    """Calculate potential evaporation using Hargreaves equation.

    Parameters
    ==========
    lat: float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    temp_min_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    source_units
        If unit is specified for the column as the second field of a ':'
        delimited column name, then the specified units and the
        'source_units' must match exactly.

        Any unit string compatible with the 'pint' library can be
        used.

        Since there are two required input columns ("temp_min_col" and
        "temp_max_col") and one optional input column ("temp_mean_col")
        you need to supply units for each input column in `source_units`.

        Command line::

            mettoolbox pet hargreaves 24 1 2 degF,degF < tmin_tmax_data.csv

        Python::

            from mettoolbox import mettoolbox as mt
            df = mt.pet.hargreaves(24,
                                   1,
                                   2,
                                   ["degF", "degF"],
                                   input_ts="tmin_tmax_data.csv")
    {input_ts}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {target_units}
    {print_input}
    {tablefmt}
    temp_mean_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`."""
    tsutils._printiso(
        pet.hargreaves(
            lat,
            temp_min_col=temp_min_col,
            temp_max_col=temp_max_col,
            temp_mean_col=temp_mean_col,
            source_units=source_units,
            input_ts=input_ts,
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            skiprows=skiprows,
            index_type=index_type,
            names=names,
            target_units=target_units,
            print_input=print_input,
        ),
        tablefmt=tablefmt,
    )


pet.hargreaves.__doc__ = hargreaves_cli.__doc__


@program.pet.command("oudin", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def oudin_cli(
    lat,
    temp_min_col=None,
    temp_max_col=None,
    temp_mean_col=None,
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
    tablefmt="csv",
):
    """Estimate PET using the formula propsed by Oudin (2005).

    This model uses daily mean temperature to estimate PET based
    on the Julian day of year and latitude. The later are used
    to estimate extraterrestrial solar radiation.

    Reference,
        Ludovic Oudin et al, Which potential evapotranspiration input for a lumped rainfall–runoff model?:
        Part 2—Towards a simple and efficient potential evapotranspiration model for rainfall–runoff modelling,
        Journal of Hydrology, Volume 303, Issues 1–4, 1 March 2005, Pages 290-306, ISSN 0022-1694,
        http://dx.doi.org/10.1016/j.jhydrol.2004.08.026.
        (http://www.sciencedirect.com/science/article/pii/S0022169404004056)

    Parameters
    ==========
    lat: float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    temp_min_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    source_units
        If unit is specified for the column as the second field of a ':'
        delimited column name, then the specified units and the
        'source_units' must match exactly.

        Any unit string compatible with the 'pint' library can be
        used.

        Since there are two required input columns ("temp_min_col" and
        "temp_max_col") and one optional input column ("temp_mean_col")
        you need to supply units for each input column in `source_units`.

        Command line::

            mettoolbox pet oudin 24 1 2 degF,degF < tmin_tmax_data.csv

        Python::

            from mettoolbox import mettoolbox as mt
            df = mt.pet.oudin(24,
                              1,
                              2,
                              ["degF", "degF"],
                              input_ts="tmin_tmax_data.csv")
    {input_ts}
    {start_date}
    {end_date}
    {dropna}
    {clean}
    {round_index}
    {skiprows}
    {index_type}
    {names}
    {target_units}
    {print_input}
    {tablefmt}
    temp_mean_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`."""
    tsutils._printiso(
        pet.oudin(
            lat,
            source_units=source_units,
            temp_min_col=temp_min_col,
            temp_max_col=temp_max_col,
            temp_mean_col=temp_mean_col,
            input_ts=input_ts,
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            skiprows=skiprows,
            index_type=index_type,
            names=names,
            target_units=target_units,
            print_input=print_input,
        ),
        tablefmt=tablefmt,
    )


pet.oudin.__doc__ = oudin_cli.__doc__


def main():
    """ Main """
    if not os.path.exists("debug_mettoolbox"):
        sys.tracebacklimit = 0
    program()


if __name__ == "__main__":
    main()
