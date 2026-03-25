import warnings
from typing import Optional, Union

import pandas as pd
import pydaymet.pet as daypet
from numpy import exp
from pydantic import PositiveInt, confloat
from tstoolbox.tstoolbox import read

from mettoolbox import utils
from mettoolbox.meteo_utils import calc_ea, calc_es, daylight_hours
from mettoolbox.mettoolbox_utils import _LOCAL_DOCSTRINGS
from mettoolbox.toolbox_utils.src.toolbox_utils import tsutils

try:
    from pydantic import validate_arguments as validate_call
except ImportError:
    from pydantic import validate_call

__all__ = [
    "blaney_criddle",
    "hamon",
    "romanenko",
    "linacre",
    "hargreaves",
    "oudin_form",
    "allen",
    "priestley_taylor",
]

warnings.filterwarnings("ignore")


def _columns(tsd, req_column_list=None, optional_column_list=None):
    if req_column_list is None:
        req_column_list = []
    if optional_column_list is None:
        optional_column_list = []
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


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Evaporation calculated according to [blaney_1952]_.

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    bright_hours_col
        The column number (data columns start at 1) or column name that holds
        the time-series of the number of bright hours each day.
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
    temp_mean_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.
    temp_min_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    k : float
        A scaling factor, defaults to 1.  This is an adjustment for local conditions,
        for example, Lu, 2005 found that k=1.2 was a better fit for the southeastern
        United States.
    ${start_date}
    ${end_date}
    ${dropna}
    ${clean}
    ${round_index}
    ${skiprows}
    ${names}
    ${target_units}
    ${print_input}
    ${tablefmt}

    Returns
    -------
    pandas.Series containing the calculated evaporation.

    Examples
    --------
    >>> et_blaney_criddle = blaney_criddle(tmean)

    Notes
    -----
    Based on equation 6 in [xu_2001]_.

    .. math:: PE=kp(0.46 * T_a + 8.13)

    References
    ----------
    .. [blaney_1952] Blaney, H. F. (1952). Determining water requirements in
       irrigated areas from climatological and irrigation data.
    .. [xu_2001] Xu, C. Y., & Singh, V. P. (2001). Evaluation and
       generalization of temperature‐based methods for calculating evaporation.
       Hydrological processes, 15(2), 305-319.
    """
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


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Hamon PET: f(Tavg, latitude)

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
    temp_mean_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.

    Returns
    -------
    pandas.Series containing the calculated evaporation.

    Examples
    --------
    >>> et_hamon = hamon(tmean, lat)

    Notes
    -----
    Following [hamon_1961]_, [oudin_2005]_, and [lu_2005]_.

    .. math:: PE = (\\frac{DL}{12})^2 exp(\\frac{T_a}{16})

    References
    ----------
    .. [hamon_1961] Hamon, W. R. (1963). Estimating potential
       evapotranspiration. Transactions of the American Society of Civil
       Engineers, 128(1), 324-338.
    .. [oudin_2005] Oudin, L., Hervieu, F., Michel, C., Perrin, C.,
       Andréassian, V., Anctil, F., & Loumagne, C. (2005). Which potential
       evapotranspiration input for a lumped rainfall–runoff model?:
       Part 2—Towards a simple and efficient potential evapotranspiration model
       for rainfall–runoff modelling. Journal of hydrology, 303(1-4), 290-306.
    .. [lu_2005] Lu et al. (2005). A comparison of six potential
       evapotranspiration methods for regional use in the southeastern United
       States. Journal of the American Water Resources Association, 41, 621-
       633.
    """
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
    )

    daylh = daylight_hours(tsd.index, lat)

    pet = (daylh / 12) ** 2 * exp(tsd["tmean:degC"] / 16)
    pet.columns = ["pet_hamon:mm"]

    if target_units != source_units:
        pet = tsutils.common_kwds(pet, source_units="mm", target_units=target_units)
    return tsutils.return_input(print_input, tsd, pet)


@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Evaporation calculated according to [romanenko_1961]_.

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    temp_min_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    rh_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily average relative humidity.
    k: float
        A scaling factor, defaults to 1.  This is an adjustment for local
        conditions, for example, Lu, 2005 found that k=1.2 was a better fit for
        the southeastern United States.
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
    temp_mean_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.

    Returns
    -------
    pandas.Series containing the calculated evaporation.

    Examples
    --------
    >>> et_romanenko = romanenko(tmean, rh)

    Notes
    -----
    Based on equation 11 in [xu_2001]_.

    .. math:: PE=4.5(1 + (\\frac{T_a}{25})^2 (1  \\frac{e_a}{e_s})

    References
    ----------
    .. [romanenko_1961] Romanenko, V. A. (1961). Computation of the autumn soil
       moisture using a universal relationship for a large area. Proc. of
       Ukrainian Hydrometeorological Research Institute, 3, 12-25.
    """
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


@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Evaporation calculated according to [linacre_1977]_.

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    lat: float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    elevation: float
        The elevation of the station in
        meters.
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
    temp_mean_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.
    temp_min_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col: str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    tdew_col:
        The column name or number (data columns start numbering at 1) in the
        input data that represents daily dewpoint temperature.
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

    Returns
    -------
    pandas.Series containing the calculated evaporation.

    Examples
    --------
    >>> et_linacre = linacre(tmean, elevation, lat)

    Notes
    -----
    Based on equation 5 in [xu_2001]_.

    .. math:: PE = \\frac{\\frac{500 T_m}{(100-A)}+15 (T_a-T_d)}{80-T_a}

    References
    -----
    .. [linacre_1977] Linacre, E. T. (1977). A simple formula for estimating
       evaporation rates in various climates, using temperature data alone.
       Agricultural meteorology, 18(6), 409-424.
    """
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


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Hargreaves PET: f(Tmin, Tmax, Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    lat : float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    temp_min_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col : str, int
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
    temp_mean_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.
    """
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


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Oudin PET: f(Tavg, latitude)

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

    Reference::

        Ludovic Oudin et al, Which potential evapotranspiration input for
        a lumped rainfall–runoff model?: Part 2—Towards a simple and efficient
        potential evapotranspiration model for rainfall–runoff modelling,
        Journal of Hydrology, Volume 303, Issues 1–4, 1 March 2005, Pages
        290-306, ISSN 0022-1694,
        http://dx.doi.org/10.1016/j.jhydrol.2004.08.026.
        (http://www.sciencedirect.com/science/article/pii/S0022169404004056)

    Parameters
    ----------
    lat : float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    temp_min_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily maximum temperature.
    temp_mean_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.
    k1:
        [optional, default to 100]

        The `k1` value is used to calibrate the equation to different
        conditions.

        The k1 parameter is a scaling parameter.
    k2:
        [optional, default to 5]

        The `k2` value is used to calibrate the equation to different
        conditions.

        The k2 parameter represents the point in degrees C at which potential
        evaporation is 0.
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


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    """
    Allen PET: f(Tmin, Tmax, Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    lat : float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    temp_min_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily minimum temperature.
    temp_max_col : str, int
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
    temp_mean_col : str, int
        The column name or number (data columns start numbering at 1) in
        the input data that represents the daily mean temperature.  If
        None will be estimated by the average of `temp_min_col` and
        `temp_max_col`.
    """
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
    return read(*read_args, **read_kwds)


@validate_call
@tsutils.doc(_LOCAL_DOCSTRINGS)
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
    target_units="mm",
    print_input=False,
):
    """
    priestley_taylor PET: f(Tmin, Tmax, Tavg, latitude)

    Average daily temperature can be supplied or if not, calculated by
    (Tmax+Tmin)/2.

    Parameters
    ----------
    ${input_ts}
    lat : float
        The latitude of the station.  Positive specifies the Northern
        Hemisphere, and negative values represent the Southern
        Hemisphere.
    lon : float
        The longitude of the station.  Positive specifies east of the
        prime meridian, and negative values represent west of the
        prime meridian.
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
    rh_col:
        The column name or number (data columns start numbering at 1) in the
        input data that represents daily average relative humidity.
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
    pe = pe.priestley_taylor().iloc[:, -1]
    return tsutils.return_input(print_input, tsd, pe)
