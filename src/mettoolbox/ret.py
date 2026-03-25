import warnings
from typing import Optional, Union

import pandas as pd
import pydaymet.pet as daypet
from pydantic import PositiveInt, confloat
from tstoolbox.tstoolbox import read

from mettoolbox.mettoolbox_utils import _LOCAL_DOCSTRINGS
from mettoolbox.toolbox_utils.src.toolbox_utils import tsutils

try:
    from pydantic import validate_arguments as validate_call
except ImportError:
    from pydantic import validate_call

__all__ = ["penman_monteith"]

warnings.filterwarnings("ignore")


def prepare_daymet(
    tmin_col, tmax_col, srad_col, dayl_col, rh_col, u2_col, source_units, target_units
):
    read_args = [tmin_col, tmax_col, srad_col, dayl_col]
    read_kwds = {
        "source_units": source_units,
        "names": ["tmin", "tmax", "srad", "dayl"],
        "target_units": ["degC", "degC", "W/m^2", "s"],
    }
    if rh_col is not None:
        read_args.append(rh_col)
        read_kwds["names"].append("rh")
        read_kwds["target_units"].append(None)
    if u2_col is not None:
        read_args.append(u2_col)
        read_kwds["names"].append("u2")
        read_kwds["target_units"].append("m/s")
    return read(*read_args, **read_kwds)


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
def penman_monteith(
    lat: confloat(ge=-90, le=90),
    lon: confloat(ge=-180, le=180),
    tmin_col: Optional[Union[PositiveInt, str, list]],
    tmax_col: Optional[Union[PositiveInt, str, list]],
    srad_col: Optional[Union[PositiveInt, str, list]],
    dayl_col: Optional[Union[PositiveInt, str, list]],
    source_units: Optional[Union[str, list]],
    rh_col=None,
    u2_col=None,
    input_ts="-",
    target_units="mm",
    print_input=False,
):
    """
    penman_monteith PET: f(Tmin, Tmax, Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    ${input_ts}
    lat : float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern Hemisphere.
    lon : float
        The longitude of the station.  Positive specifies east of the prime
        meridian, and negative values represent west of the prime meridian.
    temp_min_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    srad_col:
        The column name or number (data columns start numbering at 1) in the
        input data that represents daily solar radiation.
    dayl_col:
        The column name or number (data columns start numbering at 1) in the
        input data that represents daily day light fraction.
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
    rh_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily average relative humidity.
    u2_col:
        The column name or number (data columns start numbering at 1) in the
        input data that represents daily u2.
    ${start_date}
    ${end_date}
    ${dropna}
    ${clean}
    ${round_index}
    ${skiprows}
    ${index_type}
    ${names}
    ${target_units}
    ${print_input}
    ${tablefmt}
    """
    if isinstance(input_ts, (pd.DataFrame, pd.Series)):
        tsd = input_ts
    else:
        tsd = prepare_daymet(
            tmin_col,
            tmax_col,
            srad_col,
            dayl_col,
            rh_col,
            u2_col,
            source_units,
            target_units,
        )
    rename = {
        "tmin:degC": "tmin (degrees C)",
        "tmax:degC": "tmax (degrees C)",
        "srad:W/m^2": "srad (W/m2)",
        "dayl:s": "dayl (s)",
        "rh:": "rh",
        "u2:m/s": "u2 (m/s)",
    }
    tsd = tsd.rename(columns=rename)

    pe = daypet.PETCoords(tsd, (lon, lat))
    pe = pe.penman_monteith().iloc[:, -1]
    return tsutils.return_input(print_input, tsd, pe)
