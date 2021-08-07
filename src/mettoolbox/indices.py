# -*- coding: utf-8 -*-

from typing import Optional, Union

import pandas as pd
import typic
from standard_precip.spi import SPI
from tstoolbox import tsutils


def _nlarge_nsmall(pe_data, nlargest, nsmallest, groupby):
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
@typic.al
def spei(
    rainfall: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
    pet: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
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
):
    from tstoolbox.tstoolbox import read

    tsd = read(
        rainfall,
        pet,
        names=["rainfall", "pet"],
        source_units=source_units,
        target_units=["mm", "mm"],
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
@typic.al
def pe(
    rainfall: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
    pet: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
    source_units,
    nsmallest=None,
    nlargest=None,
    groupby="M",
    window=30,
    min_periods=None,
    center=None,
    win_type=None,
    closed=None,
    input_ts="-",
    start_date=None,
    end_date=None,
    dropna="no",
    clean=False,
    round_index=None,
    names=None,
    target_units="mm",
    print_input=False,
):
    from tstoolbox.tstoolbox import read

    tsd = read(
        rainfall,
        pet,
        names=["rainfall", "pet"],
        source_units=source_units,
        target_units=["mm", "mm"],
    )

    pe_data = tsd["rainfall:mm"] - tsd["pet:mm"]

    pe_data = tsutils._normalize_units(pe_data, "mm", target_units)

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
