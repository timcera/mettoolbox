import warnings
from typing import Optional, Union

import pandas as pd
import pydaymet.pet as daypet
from numpy import exp
from pydantic import PositiveInt, confloat, validate_arguments
from toolbox_utils import tsutils
from tstoolbox.tstoolbox import read

from . import utils
from .meteo_utils import calc_ea, calc_es, daylight_hours

warnings.filterwarnings("ignore")


def _columns(tsd, req_column_list=[], optional_column_list=[]):
    if None in req_column_list:
        raise ValueError(
            tsutils.error_wrapper(
                f"""
                You need to supply the column (name or number, data column
                numbering starts at 1) for {len(req_column_list)} time-series.

                Instead you gave {req_column_list}"""
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
            collect.append(tsd.loc[:, nloopvar])

    return collect


def _temp_read(
    temp_min_col,
    temp_max_col,
    temp_mean_col,
    source_units,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
):
    if temp_mean_col is None:
        tsd = tsutils.common_kwds(
            input_tsd=[temp_min_col, temp_max_col],
            names=["tmin", "tmax"],
            source_units=source_units,
            target_units=["degC", "degC"],
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            skiprows=skiprows,
            index_type=index_type,
        )
        tsd["tmean:degC"] = (tsd["tmin:degC"] + tsd["tmax:degC"]) / 2
    else:
        tsd = tsutils.common_kwds(
            input_tsd=[temp_min_col, temp_max_col, temp_max_col],
            names=["tmin", "tmax", "tmean"],
            source_units=source_units,
            target_units=["degC", "degC", "degC"],
            start_date=start_date,
            end_date=end_date,
            dropna=dropna,
            clean=clean,
            round_index=round_index,
            skiprows=skiprows,
            index_type=index_type,
        )
    return tsd


def _preprocess(
    input_ts,
    temp_min_col,
    temp_max_col,
    temp_mean_col,
    temp_min_required,
    temp_max_required,
    skiprows,
    names,
    index_type,
    start_date,
    end_date,
    round_index,
    dropna,
    clean,
    source_units,
):
    columns, column_names = utils._check_temperature_cols(
        temp_min_col=temp_min_col,
        temp_max_col=temp_max_col,
        temp_mean_col=temp_mean_col,
        temp_min_required=temp_min_required,
        temp_max_required=temp_max_required,
    )
    tsd = tsutils.common_kwds(
        input_ts,
        skiprows=skiprows,
        names=names,
        index_type=index_type,
        start_date=start_date,
        end_date=end_date,
        pick=columns,
        round_index=round_index,
        dropna=dropna,
        clean=clean,
    )

    if source_units is None:
        # If "source_units" keyword is None must have source_units in column
        # name.
        source_units = []
        for units in tsd.columns:
            words = units.split(":")
            if len(words) >= 2:
                source_units.append(words[1])
            else:
                raise ValueError(
                    tsutils.error_wrapper(
                        """
                        If "source_units" are not supplied as the second ":"
                        delimited field in the column name they must be
                        supplied with the "source_units" keyword.
                        """
                    )
                )
    else:
        source_units = tsutils.make_list(source_units)
    if len(source_units) != len(tsd.columns):
        raise ValueError(
            tsutils.error_wrapper(
                """
                The number of "source_units" terms must match the number of
                temperature columns.
                """
            )
        )
    interim_target_units = ["degC"] * len(tsd.columns)

    tsd = tsutils.common_kwds(
        tsd,
        source_units=source_units,
        target_units=interim_target_units,
    )

    tsd.columns = column_names

    tsd = utils._validate_temperatures(tsd, temp_min_col, temp_max_col)
    return tsd


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


@validate_arguments
def blaney_criddle(
    bright_hours_col,
    source_units: Optional[Union[str, list]],
    temp_mean_col=None,
    temp_min_col=None,
    temp_max_col=None,
    k=0.85,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    names=None,
    target_units="mm",
    print_input=False,
):
    """Evaporation calculated according to (Blaney, 1952)."""
    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        names=names,
    )
    bright_hours = tsutils.common_kwds(
        bright_hours_col,
        start_date=start_date,
        end_date=end_date,
        round_index=round_index,
        dropna=dropna,
        clean=clean,
    )

    pet = k * bright_hours * (0.46 * tsd["tmean:degC"] + 8.13)
    pet.columns = ["pet_blaney_criddle:mm"]

    if target_units != source_units:
        pet = tsutils.common_kwds(pet, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pet)


@validate_arguments
def hamon(
    lat: confloat(ge=-90, le=90),
    source_units: Optional[Union[str, list]],
    temp_mean_col=None,
    temp_min_col=None,
    temp_max_col=None,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    names=None,
    target_units=None,
    print_input=False,
):
    """Evaporation calculated according to (Hamon, 1961)."""
    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        names=names,
    )

    daylh = daylight_hours(tsd.index, lat)

    pet = (daylh / 12) ** 2 * exp(tsd["tmean:degC"] / 16)
    pet.columns = ["pet_hamon:mm"]

    if target_units != source_units:
        pet = tsutils.common_kwds(pet, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pet)


def romanenko(
    source_units: Optional[Union[str, list]],
    temp_mean_col=None,
    temp_min_col=None,
    temp_max_col=None,
    rh_col=None,
    k=4.5,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    names=None,
    target_units=None,
    print_input=False,
):
    """Evaporation calculated according to (Romanenko, 1961)."""
    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        names=names,
    )
    rh_col = tsutils.common_kwds(
        rh_col,
        start_date=start_date,
        end_date=end_date,
        round_index=round_index,
        dropna=dropna,
        clean=clean,
    )

    ea = calc_ea(tmean=tsd["tmean:degC"], rh=rh_col)
    es = calc_es(tmean=tsd["tmean:degC"])

    pet = k * (1 + tsd["tmean:degC"] / 25) ** 2 * (1 - ea / es)
    pet.columns = ["pet_romanenko:mm"]

    if target_units != source_units:
        pet = tsutils.common_kwds(pet, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pet)


def linacre(
    lat: confloat(ge=-90, le=90),
    elevation,
    source_units: Optional[Union[str, list]],
    temp_mean_col=None,
    temp_min_col=None,
    temp_max_col=None,
    tdew_col=None,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    names=None,
    target_units=None,
    print_input=False,
):
    """Evaporation calculated according to (Linacre, 1977)."""
    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        names=names,
    )
    tdew_col = tsutils.common_kwds(
        tdew_col,
        start_date=start_date,
        end_date=end_date,
        round_index=round_index,
        dropna=dropna,
        clean=clean,
    )

    if tdew_col is None:
        tdew_col = (
            0.52 * tsd["tmin:degC"]
            + 0.6 * tsd["tmax:degC"]
            - 0.009 * tsd["tmax:degC"] ** 2
            - 2
        )
    tm = tsd["tmean:degC"] + 0.006 * elevation
    pet = (500 * tm / (100 - lat) + 15 * (tsd["tmean:degC"] - tdew_col)) / (
        80 - tsd["tmean:degC"]
    )
    pet.columns = ["pet_linacre:mm"]

    if target_units != source_units:
        pet = tsutils.common_kwds(pet, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pet)


@validate_arguments
def hargreaves(
    lat: confloat(ge=-90, le=90),
    temp_min_col: Optional[Union[PositiveInt, str, list]],
    temp_max_col: Optional[Union[PositiveInt, str, list]],
    source_units: Optional[Union[str, list]],
    temp_mean_col: Optional[Union[PositiveInt, str]] = None,
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
    """hargreaves"""
    # If temp_min_col, temp_max_col, or temp_mean_col have a "," then the
    # source is the first comma delimited word, and the remaining words are
    # modifiers.
    #
    # If temp_min_col, temp_max_col, or temp_mean_col do not have a "," then
    # they are integer column numbers or string column names in "input_ts".

    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        index_type=index_type,
        names=names,
    )

    newra = utils.radiation(tsd, lat)
    tsdiff = tsd["tmax:degC"] - tsd["tmin:degC"]

    # Create new dataframe with tsd.index as index in
    # order to get all of the time components correct.
    pe = pd.DataFrame(0.0, index=tsd.index, columns=["pet_hargreaves:mm"])

    pe["pet_hargreaves:mm"] = (
        0.408
        * 0.0023
        * newra.ra.values
        * tsdiff.values**0.5
        * (tsd["tmean:degC"].values + 17.8)
    )
    if target_units != source_units:
        pe = tsutils.common_kwds(pe, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pe)


@validate_arguments
def oudin_form(
    lat: confloat(ge=-90, le=90),
    temp_min_col: Optional[Union[PositiveInt, str]],
    temp_max_col: Optional[Union[PositiveInt, str]],
    temp_mean_col: Optional[Union[PositiveInt, str]] = None,
    k1=100,
    k2=5,
    source_units=None,
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
    """oudin form"""
    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        index_type=index_type,
        names=names,
    )

    newra = utils.radiation(tsd, lat)

    # Create new dataframe with tsd.index as index in
    # order to get all of the time components correct.
    pe = pd.DataFrame(0.0, index=tsd.index, columns=["pet_oudin:mm"])

    gamma = 2.45  # the latent heat flux (MJ kg−1)
    rho = 1000.0  # density of water (kg m-3)

    pe.loc[tsd["tmean"] > k2, "pet_oudin:mm"] = (
        newra.ra / (gamma * rho) * (tsd["tmean"] + k2) / k1 * 1000
    )

    if target_units != source_units:
        pe = tsutils.common_kwds(pe, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pe)


@validate_arguments
def allen(
    lat: confloat(ge=-90, le=90),
    temp_min_col: Optional[Union[PositiveInt, str]],
    temp_max_col: Optional[Union[PositiveInt, str]],
    source_units: Optional[Union[str, list]],
    temp_mean_col: Optional[Union[PositiveInt, str]] = None,
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
    """Allen"""
    tsd = _temp_read(
        temp_min_col,
        temp_max_col,
        temp_mean_col,
        source_units,
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        index_type=index_type,
        names=names,
    )

    newra = utils.radiation(tsd, lat)

    # Create new dataframe with tsd.index as index in
    # order to get all of the time components correct.
    pe = pd.DataFrame(0.0, index=tsd.index, columns=["pet_allen:mm"])

    pe["pet_allen:mm"] = (
        0.408
        * 0.0029
        * newra.ra
        * (tsd["tmax:degC"] - tsd["tmin:degC"]) ** 0.4
        * (tsd["tmean:degC"] + 20)
    )

    if target_units != source_units:
        pe = tsutils.common_kwds(pe, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pe)


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
def priestley_taylor(
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
    """priestley_taylor"""
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
    pe = pe.priestley_taylor().iloc[:, -1]
    return tsutils.return_input(print_input, tsd, pe)


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
