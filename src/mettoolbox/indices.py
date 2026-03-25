from typing import Optional, Union

import pandas as pd
from pydantic import PositiveInt

from mettoolbox.mettoolbox_utils import _LOCAL_DOCSTRINGS
from mettoolbox.standard_precip.standard_precip.spi import SPI
from mettoolbox.toolbox_utils.src.toolbox_utils import tsutils

try:
    from pydantic import validate_arguments as validate_call
except ImportError:
    from pydantic import validate_call

__all__ = ["spei", "pe"]


def _nlarge_nsmall(
    pe_data: pd.DataFrame,
    nlargest: Optional[PositiveInt],
    nsmallest: Optional[PositiveInt],
    groupby: str,
):
    if nlargest is None and nsmallest is None:
        return pe_data

    nlarge = pd.Series()
    nsmall = pd.Series()
    if nlargest is not None:
        nlarge = pe_data.resample(groupby).apply(
            lambda x: x.nlargest(int(nlargest), x.columns[0])
        )
        nlarge = nlarge.droplevel(0)
        nlarge.sort_index(inplace=True)
        nlarge = nlarge.reindex(
            pd.date_range(start=nlarge.index[0], end=nlarge.index[-1], freq="D")
        )
    if nsmallest is not None:
        nsmall = pe_data.resample(groupby).apply(
            lambda x: x.nsmallest(int(nsmallest), x.columns[0])
        )
        nsmall = nsmall.droplevel(0)
        nsmall.sort_index(inplace=True)
        nsmall = nsmall.reindex(
            pd.date_range(start=nsmall.index[0], end=nsmall.index[-1], freq="D")
        )
    if nsmallest is not None and nlargest is None:
        return nsmall
    if nsmallest is None and nlargest is not None:
        return nlarge
    return pd.concat([nsmall, nlarge], axis="columns")


@tsutils.transform_args(source_units=tsutils.make_list)
@validate_call(config={"arbitrary_types_allowed": True})
@tsutils.doc(_LOCAL_DOCSTRINGS)
def spei(
    rainfall: Union[PositiveInt, str, pd.DataFrame],
    pet: Union[PositiveInt, str, pd.DataFrame],
    source_units,
    nsmallest=None,
    nlargest=None,
    groupby="M",
    fit_type="lmom",
    dist_type="gam",
    scale=1,
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    skiprows=None,
    index_type="datetime",
):
    """
    Standard Precipitation/Evaporation Index.

    Calculates a windows cumulative sum of daily precipitation minus
    evaporation.

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
    ${source_units}
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
    fit_type : str ("lmom" or "mle")
        Specify the type of fit to use for fitting distribution to the
        precipitation data. Either L-moments (lmom) or Maximum Likelihood
        Estimation (mle). Note use L-moments when comparing to NCAR's NCL code
        and R's packages to calculate SPI and SPEI.
    dist_type : str
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

    scale : int (default=1)
        Integer to specify the number of time periods over which the
        standardized precipitation index is to be calculated. If freq="M" then
        this is the number of months.
    ${input_ts}
    ${start_date}
    ${end_date}
    ${dropna}
    ${clean}
    ${round_index}
    ${skiprows}
    ${index_type}
    ${names}
    ${print_input}
    ${tablefmt}
    """
    from tstoolbox.tstoolbox import read

    tsd = read(
        rainfall,
        pet,
        names=["rainfall", "pet"],
        source_units=source_units,
        target_units=["mm", "mm"],
        start_date=start_date,
        end_date=end_date,
        dropna=dropna,
        clean=clean,
        round_index=round_index,
        skiprows=skiprows,
        index_type=index_type,
    )

    tsd["pe"] = tsd["rainfall:mm"] - tsd["pet:mm"]

    tsd["date"] = tsd.index

    spi = SPI()

    # def calculate(self, df: pd.DataFrame, date_col: str, precip_cols: list, freq: str="M",
    #               scale: int=1, freq_col: str=None, fit_type: str='lmom', dist_type: str='gam',
    #               **dist_kwargs) -> pd.DataFrame:

    tsd = tsutils.asbestfreq(tsd)

    ndf = spi.calculate(
        tsd,
        "date",
        "pe",
        freq=tsd.index.freqstr,
        scale=scale,
        fit_type=fit_type,
        dist_type=dist_type,
    )

    return _nlarge_nsmall(ndf, nlargest, nsmallest, groupby)


@tsutils.transform_args(source_units=tsutils.make_list)
@validate_call(config={"arbitrary_types_allowed": True})
@tsutils.doc(_LOCAL_DOCSTRINGS)
def pe(
    rainfall: Union[PositiveInt, str, pd.DataFrame],
    pet: Union[PositiveInt, str, pd.DataFrame],
    source_units,
    nsmallest=None,
    nlargest=None,
    groupby="M",
    window=30,
    min_periods=None,
    center=None,
    win_type=None,
    closed=None,
    target_units="mm",
):
    """
    Precipitation minus evaporation index.

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
    ${source_units}
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
    min_periods : int, default 170 days
        Minimum number of observations in window required to have a value
        (otherwise result is NA). For a window that is specified by an offset,
        min_periods will default to 1. Otherwise, min_periods will default to
        the size of the window.
    center : bool, default False
        Set the labels at the center of the window.
    win_type : str, default None
        Provide a window type. If None, all points are evenly weighted. See the
        notes below for further information.
    closed : str, default None
        Make the interval closed on the ‘right’, ‘left’, ‘both’ or ‘neither’
        endpoints. Defaults to ‘right’.
    ${input_ts}
    ${start_date}
    ${end_date}
    ${dropna}
    ${clean}
    ${round_index}
    ${index_type}
    ${names}
    ${target_units}
    ${print_input}
    ${tablefmt}
    """
    from tstoolbox.tstoolbox import read

    tsd = read(
        rainfall,
        pet,
        names=["rainfall", "pet"],
        source_units=source_units,
        target_units=["mm", "mm"],
    )

    pe_data = tsd["rainfall:mm"] - tsd["pet:mm"]

    pe_data = tsutils.common_kwds(
        input_tsd=pe_data, source_units=["mm"], target_units=target_units
    )

    pe_data = (
        pe_data.astype(float)
        .rolling(
            window,
            min_periods=min_periods,
            center=center,
            win_type=win_type,
            closed=closed,
        )
        .sum()
    )

    return _nlarge_nsmall(pe_data, nlargest, nsmallest, groupby)
