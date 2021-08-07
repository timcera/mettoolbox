# -*- coding: utf-8 -*-

import os.path
import sys
import warnings
from typing import Optional, Union

import pandas as pd
import typic
from mando import Program
from mando.rst_text_formatter import RSTHelpFormatter
from standard_precip.spi import SPI
from tstoolbox import tsutils

program = Program("mettoolbox", "0.0")

from . import disaggregate, indices, pet

warnings.filterwarnings("ignore")

program.add_subprog("disaggregate")
program.add_subprog("pet")
program.add_subprog("indices")

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
    ----------
    method: str
        This is the method that will be used to disaggregate
        the daily evaporation data.

        There are two methods, a trapezoidal shape from sunrise to
        sunset called "trap" and a fixed, smooth curve starting at 0700
        (7 am) and stopping at 1900 (7 pm) called "fixed".

    {source_units}

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
    ----------
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
    columns=None,
    masterstation_hour_col=None,
):
    """Disaggregate daily precipitation to hourly precipitation.

    Parameters
    ----------
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

    {columns}

    masterstation_hour_col
        The column number or name that contains the hourly data used as the reference
        station.
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
            masterstation_hour_col=masterstation_hour_col,
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
    ----------
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
    ----------
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
    ----------
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


@program.pet.command("allen", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def allen_cli(
    lat,
    temp_min_col,
    temp_max_col,
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
    """Allen PET: f(Tmin, Tmax, Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
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

            mettoolbox pet allen 24 1 2 degF,degF < tmin_tmax_data.csv

        Python::

            from mettoolbox import mettoolbox as mt
            df = mt.pet.allen(24,
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
        pet.allen(
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


pet.allen.__doc__ = allen_cli.__doc__


@program.pet.command("hamon", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def hamon_cli(
    lat,
    temp_min_col,
    temp_max_col,
    temp_mean_col=None,
    k=1.2,
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
    """Hamon PET: f(Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
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

    k: float
        A scaling factor, defaults to 1.  This is an adjustment for local conditions,
        for example, Lu, 2005 found that k=1.2 was a better fit for the southeastern
        United States.

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

            mettoolbox pet hamon 24 1 2 degF,degF < tmin_tmax_data.csv

        Python::

            from mettoolbox import mettoolbox as mt
            df = mt.pet.hamon(24,
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
        `temp_max_col`.

    References
    ----------
    Lu et al. (2005). A comparison of six potential evaportranspiration methods for
    regional use in the southeastern United States. Journal of the American Water
    Resources Association, 41, 621- 633."""
    tsutils._printiso(
        pet.hamon(
            lat,
            temp_min_col=temp_min_col,
            temp_max_col=temp_max_col,
            temp_mean_col=temp_mean_col,
            k=k,
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


pet.hamon.__doc__ = hamon_cli.__doc__


@program.pet.command("hargreaves", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def hargreaves_cli(
    lat,
    temp_min_col,
    temp_max_col,
    source_units,
    temp_mean_col=None,
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
    """Hargreaves PET: f(Tmin, Tmax, Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
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


@program.pet.command("oudin_form", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def oudin_form_cli(
    lat,
    temp_min_col,
    temp_max_col,
    temp_mean_col=None,
    k1=100,
    k2=5,
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
    """Oudin PET: f(Tavg, latitude)

    This model uses daily mean temperature to estimate PET based
    on the Julian day of year and latitude. The later are used
    to estimate extraterrestrial solar radiation.

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    The constants `k1` and `k2` are used in the generic form of the equation to
    adjust the PET.

    The defaults for k1 and k2 for this function are from Oudin with k1=100 and
    k2=5.

    Jensen-Haise presented k1=40, and k2=0,

    Mcguiness presented k1=68, and k2=5.

    The k2 parameter represents the point in degrees C at which potential
    evaporation is 0.  The k1 parameter is a scaling parameter.

    Reference,
        Ludovic Oudin et al, Which potential evapotranspiration input for
        a lumped rainfall–runoff model?: Part 2—Towards a simple and efficient
        potential evapotranspiration model for rainfall–runoff modelling,
        Journal of Hydrology, Volume 303, Issues 1–4, 1 March 2005, Pages
        290-306, ISSN 0022-1694,
        http://dx.doi.org/10.1016/j.jhydrol.2004.08.026.
        (http://www.sciencedirect.com/science/article/pii/S0022169404004056)

    Parameters
    ----------
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
        If unit is specified for the column as the second field of a
        ':' delimited column name, then the specified units and the
        'source_units' must match exactly.

        Any unit string compatible with the 'pint' library can be
        used.

        Since there are two required input columns ("temp_min_col" and
        "temp_max_col") and one optional input column ("temp_mean_col")
        you need to supply units for each input column in `source_units`.

        Command line::

            mettoolbox pet oudin_form 24 1 2 degF,degF < tmin_tmax_data.csv

        Python::

            from mettoolbox import mettoolbox as mt
            df = mt.pet.oudin_form(24, 1, 2, ["degF", "degF"], input_ts="tmin_tmax_data.csv")

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
        pet.oudin_form(
            lat,
            source_units=source_units,
            temp_min_col=temp_min_col,
            temp_max_col=temp_max_col,
            temp_mean_col=temp_mean_col,
            k1=k1,
            k2=k2,
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


pet.oudin_form.__doc__ = oudin_form_cli.__doc__


@program.indices.command("spei", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def spei_cli(
    rainfall,
    pet,
    source_units,
    nsmallest=None,
    nlargest=None,
    groupby="M",
    fit_type="lmom",
    dist_type="gam",
    scale=1,
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
    tablefmt="csv",
):
    """Standard Precipitation/Evaporation Index.

    Calculates a windows cumulative sum of daily precipitation minus evaporation.

    Parameters
    ----------
    rainfall
        A csv, wdm, hdf5, xlsx file or a pandas DataFrame or Series or
        an integer column or string name of standard input.

        Represents a daily time-series of precipitation in units specified in
        `source_units`.

    pet
        A csv, wdm, hdf5, xlsx file or a pandas DataFrame or Series or
        an integer column or string name of standard input.

        Represents a daily time-series of evaporation in units specified in
        `source_units`.

    {source_units}

    nsmallest : int
        [optional, default is None]

        Return the "n" days with the smallest precipitation minus evaporation
        index value within the `groupby` pandas offset period.

        Cannot assign both `nsmallest` and `nlargest` keywords.

    nlargest : int
        [optional, default is None]

        Return the "n" days with the largest precipitation minus evaporation
        index value within the `groupby` pandas offset period.

        Cannot assign both `nsmallest` and `nlargest` keywords.

    groupby : str
        Pandas offset period string representing the time over which the
        `nsmallest` or `nlargest` values would be evaluated.

    fit_type: str ("lmom" or "mle")
        Specify the type of fit to use for fitting distribution to the
        precipitation data. Either L-moments (lmom) or Maximum Likelihood
        Estimation (mle). Note use L-moments when comparing to NCAR's NCL code
        and R's packages to calculate SPI and SPEI.

    dist_type: str
        The distribution type to fit using either L-moments (fit_type="lmom")
        or MLE (fit_type="mle").

        +-----------+---------------------------+-----------+----------+
        | dist_type | Distribution              | fit_type  | fit_type |
        |           |                           | lmom      | mle      |
        +===========+===========================+===========+==========+
        | gam       | Gamma                     | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | exp       | Exponential               | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | gev       | Generalized Extreme Value | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | gpa       | Generalized Pareto        | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | gum       | Gumbel                    | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | nor       | Normal                    | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | pe3       | Pearson III               | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | wei       | Weibull                   | X         | X        |
        +-----------+---------------------------+-----------+----------+
        | glo       | Generalized Logistic      |           | X        |
        +-----------+---------------------------+-----------+----------+
        | gno       | Generalized Normal        |           | X        |
        +-----------+---------------------------+-----------+----------+
        | kap       | Kappa                     |           | X        |
        +-----------+---------------------------+-----------+----------+
        | wak       | Wakeby                    | X         |          |
        +-----------+---------------------------+-----------+----------+

    scale: int (default=1)
        Integer to specify the number of time periods over which the
        standardized precipitation index is to be calculated. If freq="M" then
        this is the number of months.

    {input_ts}

    {start_date}

    {end_date}

    {dropna}

    {clean}

    {round_index}

    {skiprows}

    {index_type}

    {names}

    {print_input}

    {tablefmt}
    """
    tsutils._printiso(
        indices.spei(
            rainfall,
            pet,
            source_units,
            nsmallest=nsmallest,
            nlargest=nlargest,
            groupby=groupby,
            fit_type=fit_type,
            dist_type=dist_type,
            scale=scale,
            input_ts=input_ts,
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            skiprows=skiprows,
            index_type=index_type,
            names=names,
            print_input=print_input,
        ),
        tablefmt=tablefmt,
    )


indices.spei.__doc__ = spei_cli.__doc__


@program.indices.command("pe", formatter_class=RSTHelpFormatter, doctype="numpy")
@tsutils.doc(_LOCAL_DOCSTRINGS)
def pe_cli(
    rainfall,
    pet,
    source_units,
    nsmallest=None,
    nlargest=None,
    groupby="M",
    window=30,
    min_periods=None,
    center=False,
    win_type=None,
    closed=None,
    input_ts="-",
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    index_type="datetime",
    names=None,
    target_units="mm",
    print_input=False,
    tablefmt="csv",
):
    """Precipitation minus evaporation index.

    Calculates a windows cumulative sum of daily precipitation minus evaporation.

    Parameters
    ----------
    rainfall
        A csv, wdm, hdf5, xlsx file or a pandas DataFrame or Series or
        an integer column or string name of standard input.

        Represents a daily time-series of precipitation in units specified in
        `source_units`.

    pet
        A csv, wdm, hdf5, xlsx file or a pandas DataFrame or Series or
        an integer column or string name of standard input.

        Represents a daily time-series of evaporation in units specified in
        `source_units`.

    {source_units}

    nsmallest : int
        [optional, default is None]

        Return the "n" days with the smallest precipitation minus evaporation
        index value within the `groupby` pandas offset period.

        Cannot assign both `nsmallest` and `nlargest` keywords.

    nlargest : int
        [optional, default is None]

        Return the "n" days with the largest precipitation minus evaporation
        index value within the `groupby` pandas offset period.

        Cannot assign both `nsmallest` and `nlargest` keywords.

    groupby : str
        Pandas offset period string representing the time over which the
        `nsmallest` or `nlargest` values would be evaluated.

    window : int
        [optional, default is 30]

        Size of the moving window. This is the number of observations used for
        calculating the statistic. Each window will be a fixed size.

        If its an offset then this will be the time period of each window. Each
        window will be a variable sized based on the observations included in
        the time-period. This is only valid for datetimelike indexes.

    min_periods: int, default 170 days
        Minimum number of observations in window required to have a value
        (otherwise result is NA). For a window that is specified by an offset,
        min_periods will default to 1. Otherwise, min_periods will default to
        the size of the window.

    center: bool, default False
        Set the labels at the center of the window.

    win_type: str, default None
        Provide a window type. If None, all points are evenly weighted. See the
        notes below for further information.

    closed: str, default None
        Make the interval closed on the ‘right’, ‘left’, ‘both’ or ‘neither’
        endpoints. Defaults to ‘right’.

    {input_ts}

    {start_date}

    {end_date}

    {dropna}

    {clean}

    {round_index}

    {index_type}

    {names}

    {target_units}

    {print_input}

    {tablefmt}
    """
    tsutils._printiso(
        indices.pe(
            rainfall,
            pet,
            source_units,
            nsmallest=nsmallest,
            nlargest=nlargest,
            groupby=groupby,
            window=window,
            min_periods=min_periods,
            center=center,
            win_type=win_type,
            closed=closed,
            input_ts=input_ts,
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            names=names,
            target_units=target_units,
            print_input=print_input,
        ),
        tablefmt=tablefmt,
    )


indices.pe.__doc__ = pe_cli.__doc__


def main():
    """Main"""
    if not os.path.exists("debug_mettoolbox"):
        sys.tracebacklimit = 0
    program()


if __name__ == "__main__":
    main()
