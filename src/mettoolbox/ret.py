import warnings
from typing import Optional, Union

import pandas as pd
import pydaymet.pet as daypet
from pydantic import PositiveInt, confloat, validate_arguments
from toolbox_utils import tsutils
from tstoolbox.tstoolbox import read

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
    tsd = read(*read_args, **read_kwds)
    return tsd


@validate_arguments
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
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
    names=None,
    target_units="mm",
    print_input=False,
):
    """reference penman-monteith"""
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
