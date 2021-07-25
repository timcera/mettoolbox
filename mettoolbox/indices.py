# -*- coding: utf-8 -*-

from typing import Optional, Union

import pandas as pd
import typic
from standard_precip.spi import SPI
from tstoolbox import tsutils


@typic.al
def spei(
    rainfall: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
    pet: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
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
    print_input=False,
):

    tsd = tsutils.common_kwds(
        input_ts,
        skiprows=skiprows,
        names=names,
        index_type=index_type,
        start_date=start_date,
        end_date=end_date,
        round_index=round_index,
        dropna=dropna,
        clean=clean,
        source_units=source_units,
    )

    spi = SPI()

    # def calculate(self, df: pd.DataFrame, date_col: str, precip_cols: list, freq: str="M",
    #               scale: int=1, freq_col: str=None, fit_type: str='lmom', dist_type: str='gam',
    #               **dist_kwargs) -> pd.DataFrame:

    spei_data = tsd[rainfall] - tsd[pet]
    spei_data = spei_data.append(tsd.index)

    ndf = spi.calculate(tsd, -1, 1)

    print(ndf)


@typic.al
def pe(
    rainfall: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
    pet: Optional[Union[tsutils.IntGreaterEqualToOne, str]],
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
    print_input=False,
):

    tsd = tsutils.common_kwds(
        input_ts,
        skiprows=skiprows,
        names=names,
        index_type=index_type,
        start_date=start_date,
        end_date=end_date,
        round_index=round_index,
        dropna=dropna,
        clean=clean,
        source_units=source_units,
    )

    spi = SPI()

    # def calculate(self, df: pd.DataFrame, date_col: str, precip_cols: list, freq: str="M",
    #               scale: int=1, freq_col: str=None, fit_type: str='lmom', dist_type: str='gam',
    #               **dist_kwargs) -> pd.DataFrame:

    spei_data = tsd[rainfall] - tsd[pet]
    spei_data = spei_data.append(tsd.index)

    ndf = spi.calculate(tsd, -1, 1)

    print(ndf)
