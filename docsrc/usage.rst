=====
Usage
=====

Command Line
------------

Type::
    
    mettoolbox --help

for a list of available sub-commands.

::

    usage: mettoolbox disaggregate [-h]
                                   {temperature,humidity,wind_speed,radiation,precipitation,evaporation}
                                   ...
    
    positional arguments:
      {temperature,humidity,wind_speed,radiation,precipitation,evaporation}
        temperature         Disaggregate daily temperature to hourly temperature.
        humidity            Disaggregate daily relative humidity to hourly
                            humidity.
        wind_speed          Disaggregate daily wind speed to hourly wind speed.
        radiation           Disaggregate daily radiation to hourly radiation.
        precipitation       Disaggregate daily precipitation to hourly
                            precipitation.
        evaporation         Disaggregate daily evaporation to hourly evaporation.
    
    optional arguments:
      -h, --help            show this help message and exit

::

    usage: mettoolbox pet [-h] {hargreaves} ...
    
    positional arguments:
      {hargreaves}
        hargreaves  Calculate potential evaporation using Hargreaves equation.
    
    optional arguments:
      -h, --help    show this help message and exit
