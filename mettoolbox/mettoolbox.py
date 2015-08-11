#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys
import os.path
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import mando

from tstoolbox import tsutils

@mando.command()
def PET_hargreaves(latitude,
                   tmax=None,
                   tmin=None,
                   input_ts='-',
                   start_date=None,
                   end_date=None,
                   float_format='%g',
                   print_input=''):
    '''
    Calculate potential evaporation as expected from a shallow body of water
    using the Hargreaves equation which needs the daily maximum and minimum
    temperatures.  Input is degrees C. and returns mm/day.

    :param -i, --input_ts <str>:  Filename with data in 'ISOdate,value' format or '-'
        for stdin.
    :param -s, --start_date <str>:  The start_date of the series in ISOdatetime format,
        or 'None' for beginning.
    :param -e, --end_date <str>:  The end_date of the series in ISOdatetime format, or
        'None' for end.
    :param latitude <float>: Latitude of the station.
    :param tmax: Specify comma separated column names or column numbers that
                 represent the daily maximum temperature in degrees C.  The
                 default is None, and if None there has to be an even number of
                 columns and tmax is the first half of the columns, and tmin is
                 the last half of the columns.
    :param tmin: Specify comma separated column names or column numbers that
                 represent the daily minimum temperature in degrees C.  The
                 default is None, and if None there has to be an even number of
                 columns and tmax is the first half of the columns, and tmin is
                 the last half of the columns.
    '''
    tsd = tsutils.common_kwds(tsutils.read_iso_ts(input_ts),
                             start_date=start_date,
                             end_date=end_date,
                             pick=None)
    if tmax is None and tmin is None:
        tmaxcol = tsd.columns[:len(tsd.columns)/2]
        tmincol = tsd.columns[len(tsd.columns)/2:]
        if len(tsd.columns) % 2 == 1:
            raise ValueError('''
*
*   Without explicitly defining tmax and tmin columns in the input dataset, the
*   first half of the columns are tmax and the second half are tmin, which
*   means that you need an even number of columns.  Instead there are {0}.
*
'''.format(len(tsd.columns)))
    elif tmax is None or tmin is None:
        raise ValueError('''
*
*   Either tmax and tmin must be None OR tmax and tmin must have the same
*   number of comma separated columns names/numbers.
*
''')
    else:
        tmaxcol = tmax.split(',')
        tmincol = tmin.split(',')

    tmaxdf = tsd[tmaxcol]
    tmindf = tsd[tmincol]

    if pd.np.any(tmindf.values > tmaxdf.values):
        raise ValueError('''
*
*   There is at least one day where the minimum temperature is greater than the
*   maximum temperature.
*
''')

    # 'Roll-out' the distribution from day to day.
    jday = pd.np.arange(1, 367)

    # calculate right ascension
    dec = 0.4102*pd.np.sin((2.0*pd.np.pi*(jday - 80.0))/365.0)
    lrad = latitude*pd.np.pi/180.0
    s = pd.np.arccos(-pd.np.tan(dec)*pd.np.tan(lrad))
    ra = 118.0/pd.np.pi*(s*pd.np.sin(lrad)*pd.np.sin(dec) +
                         pd.np.cos(lrad)*pd.np.cos(dec)*pd.np.sin(s))

    # ra just covers 1 year - need to map onto all years...
    newra = tmindf.copy()
    for day in jday:
        newra[newra.index.dayofyear == day] = ra[day - 1]

    tsavg = (tmaxdf.values + tmindf.values)/2.0

    tsdiff = tmaxdf.values - tmindf.values

    # Copy tsavg in order to get all of the time components correct.
    pe = tmaxdf.copy()
    pe.values[:] = 0.408*0.0023*newra*(tsavg + 17.8)*pd.np.sqrt(abs(tsdiff))
    pe.columns = ['PET_hargreaves_{0}'.format(i) for i in range(len(pe.columns))]
    return tsutils.print_input(print_input, tsd, pe, None,
                               float_format=float_format)


@mando.command()
def daily_to_hourly_trapezoid(
                   latitude,
                   input_ts='-',
                   start_date=None,
                   end_date=None,
                   float_format='%g',
                   print_input=''):
    '''
    Daily to hourly disaggregation based on a trapezoidal shape.
    '''
    tsd = tsutils.common_kwds(tsutils.read_iso_ts(input_ts),
                             start_date=start_date,
                             end_date=end_date,
                             pick=None)
    lrad = latitude*np.pi/180.0

    ad = 0.40928*np.cos(0.0172141*(172 - tseries.index.dayofyear))
    ss = np.sin(lrad)*np.sin(ad)
    cs = np.cos(lrad)*np.cos(ad)
    x2 = -ss/cs
    delt = 7.6394*(np.pi/2.0 - np.arctan(x2/np.square(1 - x2**2)))
    sunr = 12.0 - delt/2.0

    #develop hourly distribution given sunrise,
    #sunset and length of day (DELT)
    dtr2 = delt / 2.0
    dtr4 = delt / 4.0
    crad = 2.0/3.0/dtr2*tseries.values/60 # using minutes...
    tr2 = sunr + dtr4
    tr3 = tr2 + dtr2
    tr4 = tr3 + dtr4

    sdate = datetime.datetime(tseries.index[0].year, tseries.index[0].month,
            tseries.index[0].day)
    edate = datetime.datetime(tseries.index[-1].year, tseries.index[-1].month,
            tseries.index[-1].day) + datetime.timedelta(days=1) - datetime.timedelta(hours=1)
    datevalue = pandas.DatetimeIndex(start=sdate, end=edate,
            freq='MIN')
    fdata = pandas.Series([np.nan]*(len(datevalue)), index=datevalue)
    fdata[0] = 0.0
    fdata[-1] = 0.0
    for index in range(len(sunr)):
        cdate = tseries.index[index]
        fdata[datetime.datetime(cdate.year, cdate.month, cdate.day, int(sunr[index]), int((sunr[index] - int(sunr[index]))*60))] = 0.0
        fdata[datetime.datetime(cdate.year, cdate.month, cdate.day, int(tr4[index]), int((tr4[index] - int(tr4[index]))*60))] = 0.0
        fdata[datetime.datetime(cdate.year, cdate.month, cdate.day, int(tr2[index]), int((tr2[index] - int(tr2[index]))*60))] = crad[index]
        fdata[datetime.datetime(cdate.year, cdate.month, cdate.day, int(tr3[index]), int((tr3[index] - int(tr3[index]))*60))] = crad[index]
    fdata = fdata.interpolate('linear')

    fdata = fdata.fillna(0.0)

    hourly = fdata.asfreq('H').index
    hourly = pandas.Series([0.0]*len(hourly), index=hourly)

    for index in range(len(hourly)):
        hourly[index] = sum(fdata[index*60:(index + 1)*60])
    return hourly


def main():
    ''' Main '''
    if not os.path.exists('debug_mettoolbox'):
        sys.tracebacklimit = 0
    mando.main()

if __name__ == '__main__':
    main()
