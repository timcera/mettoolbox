# -*- coding: utf-8 -*-
"""
Functions for calculation of potential and actual evaporation
from meteorological data.

Potential and actual evaporation functions
==========================================

        - E0: Calculate Penman (1948, 1956) open water evaporation.
        - Em: Calculate evaporation according to Makkink (1965).
        - Ept: Calculate evaporation according to Priestley and Taylor (1972).
        - ET0pm: Calculate Penman Monteith reference evaporation short grass.
        - Epm: Calculate Penman-Monteith evaporation (actual evapotranspiration).
        - ra: Calculate aerodynamic resistance from windspeed and
          roughnes parameters.
        - tvardry: calculate sensible heat flux from temperature variations.
        - gash79: Gash (1979) analytical rainfall interception model.

Requires and imports scipy and meteolib modules.
Compatible with Python 2.7.3.

Function descriptions
=====================

"""

import scipy

from . import meteolib

__author__ = "Dr. Maarten J. Waterloo <maarten.waterloo@acaciawater.com>"
__version__ = "1.0"
__release__ = "1.0.1"
__date__ = "June 2016"

# 14 June 2016: Fixed error in Epm function: changed multiplication by ra
# to division by ra. Thanks Spencer Whitman for pointing this out.


# Make a help entry for this library
def evaplib():
    """
    Evaplib: Python libray for calculation of evaporation from meteorological data.

    Parameters
    ----------
    E0:
        Calculate Penman (1948, 1956) open water evaporation.
    Em:
        Calculate evaporation according to Makkink (1965).
    Ept:
        Calculate evaporation according to Priestley and Taylor (1972).
    ET0pm:
        Calculate Penman Monteith reference evaporation short grass (FAO).
    Epm:
        Calculate Penman Monteith reference evaporation (Monteith, 1965).
    ra:
        Calculate  from windspeed and roughnes parameters.
    tvardry:
        Calculate sensible heat flux from temperature variations (Vugts et al., 1993).
    gash79:
        Calculate rainfall interception (Gash, 1979).
    Author: Dr. Maarten J. Waterloo <maarten.waterloo@acaciawater.com>.
    Version 1.0.
    Date: Sep 2012, last modified November June 2016.

    """
    print("A libray with Python functions for calculation of")
    print("evaporation from meteorological and vegetation data.\n")
    print("Functions:\n")
    print("- E0: Calculate Penman (1948, 1956) (open water) evaporation")
    print("- Em: Calculate evaporation according to Makkink (1965)")
    print("- Ept: Calculate evaporation according to Priestley and Taylor (1972).")
    print("- ET0pm: Calculate Penman Monteith reference evaporation short grass.")
    print("- Epm: Calculate Penman Monteith evaporation (Monteith, 1965).")
    print("- ra: Calculate aerodynamic resistance.")
    print(
        "- tvardry: calculate sensible heat flux from temperature variations \
          (Vugts et al., 1993)."
    )
    print("- gash79: calculate rainfall interception (Gash, 1979).\n")
    print(("Author: ", __author__))
    print(("Version: ", __version__))
    print(("Date: ", __date__))


def ra(z=float, z0=float, d=float, u=scipy.array([])):

    """
    Function to calculate aerodynamic resistance from windspeed:


    .. math::
        r_a = \\frac{\\left[\\ln\\frac{z-d}{z_0}\\right]^2}{k^2 \\cdot u_z}

    where k is the von Karman constant set at 0.4.

    Parameters:
        - z: measurement height [m].
        - z0: roughness length [m].
        - d: displacement length [m].
        - u: (array of) wind speed measured at height z [m s-1].

    Returns:
        - ra: (array of) aerodynamic resistance [s m-1].

    References
    ----------

    A.S. Thom (1075), Momentum, mass and heat exchange of plant communities,
    In: Monteith, J.L. Vegetation and the Atmosphere, Academic Press, London.
    p. 57–109.

    Examples
    --------

        >>> ra(3,0.12,2.4,5.0)
        3.2378629924752942
        >>> u=([2,4,6])
        >>> ra(3,0.12,2.4,u)
        array([ 8.09465748,  4.04732874,  2.69821916])

    """

    # Test input array/value
    u = meteolib._arraytest(u)

    # Calculate ra
    ra = (scipy.log((z - d) / z0)) ** 2 / (0.16 * u)
    return ra  # aerodynamic resistanc in s/m


def E0(
    airtemp=scipy.array([]),
    rh=scipy.array([]),
    airpress=scipy.array([]),
    Rs=scipy.array([]),
    Rext=scipy.array([]),
    u=scipy.array([]),
    alpha=0.08,
    Z=0.0,
):

    """
    Function to calculate daily Penman (open) water evaporation estimates:

    .. math::
        E_0 = \\frac{R_n \\cdot \\Delta}{\\lambda \\cdot (\\Delta + \\gamma)} + \\frac{6430000 \\cdot E_a \\cdot \\gamma}{\\lambda \\cdot (\\Delta+\\gamma)}

    Parameters:
        - airtemp: (array of) daily average air temperatures [Celsius].
        - rh: (array of) daily average relative humidity [%].
        - airpress: (array of) daily average air pressure data [Pa].
        - Rs: (array of) daily incoming solar radiation [J m-2 day-1].
        - Rext: (array of) daily extraterrestrial radiation [J m-2 day-1].
        - u: (array of) daily average wind speed at 2 m [m s-1].
        - alpha: albedo [-] set at 0.08 for open water by default.
        - Z: (array of) site elevation, default is 0 m a.s.l.

    Returns:
        - E0: (array of) Penman open water evaporation values [mm day-1].

    Notes
    -----

    Meteorological parameters measured at 2 m above the surface. Albedo
    alpha set by default at 0.08 for open water (Valiantzas, 2006).

    References
    ----------

    - H.L. Penman (1948). Natural evaporation from open water, bare soil\
    and grass. Proceedings of the Royal Society of London. Series A.\
    Mathematical and Physical Sciences 193: 120-145.
    - H.L. Penman (1956). Evaporation: An introductory survey. Netherlands\
    Journal of Agricultural Science 4: 9-29.
    - J.D. Valiantzas (2006). Simplified versions for the Penman\
    evaporation equation using routine weather data. J. Hydrology 331:\
    690-702.

    Examples
    --------

        >>> # With single values and default albedo/elevation
        >>> E0(20.67,67.0,101300.0,22600000.,42000000.,3.2)
        6.6029208786994467
        >>> # With albedo is 0.18 instead of default and default elevation
        >>> E0(20.67,67.0,101300.0,22600000.,42000000.,3.2,alpha=0.18)
        5.9664248091431968
        >>> # With standard albedo and Z= 250.0 m
        >>> E0(20.67,67.0,101300.0,22600000.,42000000.,3.2,Z=250.0)
        6.6135588207586284
        >>> # With albedo alpha = 0.18 and elevation Z = 1000 m a.s.l.
        >>> E0(20.67,67.0,101300.0,22600000.,42000000.,3.2,0.18,1000.)
        6.00814764682986

    """

    # Test input array/value
    airtemp, rh, airpress, Rs, Rext, u = meteolib._arraytest(
        airtemp, rh, airpress, Rs, Rext, u
    )

    # Set constants
    sigma = 4.903e-3  # Stefan Boltzmann constant J/m2/K4/d

    # Calculate Delta, gamma and lambda
    DELTA = meteolib.Delta_calc(airtemp)  # [Pa/K]
    gamma = meteolib.gamma_calc(airtemp, rh, airpress)  # [Pa/K]
    Lambda = meteolib.L_calc(airtemp)  # [J/kg]

    # Calculate saturated and actual water vapour pressures
    es = meteolib.es_calc(airtemp)  # [Pa]
    ea = meteolib.ea_calc(airtemp, rh)  # [Pa]

    # calculate radiation components (J/m2/day)
    Rns = (1.0 - alpha) * Rs  # Shortwave component [J/m2/d]
    Rs0 = (0.75 + 2e-5 * Z) * Rext  # Calculate clear sky radiation Rs0
    f = 1.35 * Rs / Rs0 - 0.35
    epsilom = 0.34 - 0.14 * scipy.sqrt(ea / 1000)
    Rnl = f * epsilom * sigma * (airtemp + 273.15) ** 4  # Longwave component [J/m2/d]
    Rnet = Rns - Rnl  # Net radiation [J/m2/d]
    Ea = (1 + 0.536 * u) * (es / 1000 - ea / 1000)
    E0 = (
        DELTA / (DELTA + gamma) * Rnet / Lambda
        + gamma / (DELTA + gamma) * 6430000 * Ea / Lambda
    )
    return E0


def ET0pm(
    airtemp=scipy.array([]),
    rh=scipy.array([]),
    airpress=scipy.array([]),
    Rs=scipy.array([]),
    Rext=scipy.array([]),
    u=scipy.array([]),
    Z=0.0,
):

    """
    Function to calculate daily Penman Monteith reference evaporation estimates.

    Parameters:
        - airtemp: (array of) daily average air temperatures [Celsius].
        - rh: (array of) daily average relative humidity values [%].
        - airpress: (array of) daily average air pressure data [hPa].
        - Rs: (array of) total incoming shortwave radiation [J m-2 day-1].
        - Rext: Incoming shortwave radiation at the top of the atmosphere\
        [J m-2 day-1].
        - u: windspeed [m s-1].
        - Z: elevation [m], default is 0 m a.s.l.

    Returns:
        - ET0pm: (array of) Penman Monteith reference evaporation (short\
        grass with optimum water supply) values [mm day-1].

    Notes
    -----

    Meteorological measuements standard at 2 m above soil surface.

    References
    ----------

    R.G. Allen, L.S. Pereira, D. Raes and M. Smith (1998). Crop
    evapotranspiration - Guidelines for computing crop water requirements -
    FAO Irrigation and drainage paper 56. FAO - Food and Agriculture
    Organization of the United Nations, Rome, 1998.
    (http://www.fao.org/docrep/x0490e/x0490e07.htm)

    Examples
    --------

        >>> ET0pm(20.67,67.0,101300.0,22600000.,42000000.,3.2)
        4.7235349721073039

    """

    # Test input array/value
    airtemp, rh, airpress, Rs, Rext, u = meteolib._arraytest(
        airtemp, rh, airpress, Rs, Rext, u
    )

    # Set constants
    albedo = 0.23  # short grass albedo
    sigma = 4.903e-3  # Stefan Boltzmann constant J/m2/K4/d

    # Calculate Delta, gamma and lambda
    DELTA = meteolib.Delta_calc(airtemp)  # [Pa/K]
    gamma = meteolib.gamma_calc(airtemp, rh, airpress)  # [Pa/K]
    Lambda = meteolib.L_calc(airtemp)  # [J/kg]

    # Calculate saturated and actual water vapour pressures
    es = meteolib.es_calc(airtemp)  # [Pa]
    ea = meteolib.ea_calc(airtemp, rh)  # [Pa]

    Rns = (1.0 - albedo) * Rs  # Shortwave component [J/m2/d]
    # Calculate clear sky radiation Rs0
    Rs0 = (0.75 + 2e-5 * Z) * Rext  # Clear sky radiation [J/m2/d]
    f = 1.35 * Rs / Rs0 - 0.35
    epsilom = 0.34 - 0.14 * scipy.sqrt(ea / 1000)
    Rnl = f * epsilom * sigma * (airtemp + 273.15) ** 4  # Longwave component [J/m2/d]
    Rnet = Rns - Rnl  # Net radiation [J/m2/d]
    ET0pm = (
        DELTA / 1000.0 * Rnet / Lambda
        + 900.0 / (airtemp + 273.16) * u * (es - ea) / 1000 * gamma / 1000
    ) / (DELTA / 1000.0 + gamma / 1000 * (1.0 + 0.34 * u))
    return ET0pm  # FAO reference evaporation [mm/day]


def Em(
    airtemp=scipy.array([]),
    rh=scipy.array([]),
    airpress=scipy.array([]),
    Rs=scipy.array([]),
):

    """
    Function to calculate Makkink evaporation (in mm/day):

    .. math::
        E_m = 0.65 \\frac{R_s}{\\lambda} \\cdot \\frac{\\Delta}{\\Delta + \\gamma}

    The Makkink evaporation is a reference crop evaporation. It is a reference
    crop evaporation equation based on the Penman open water equation and
    represents evapotranspiration from short, well-watered grassland under
    Dutch climate conditions. Makkink reference evaporation values are
    published daily by the Royal Netherlands Meteorological Institute (KNMI)
    in the Netherlands. Values are used in combination with crop factors to
    provide daily estimates of actual crop evaporation for many crop types.

    Parameters:
        - airtemp: (array of) daily average air temperatures [Celsius].
        - rh: (array of) daily average relative humidity values [%].
        - airpress: (array of) daily average air pressure data [Pa].
        - Rs: (array of) average daily incoming solar radiation [J m-2 day-1].

    Returns:
        - Em: (array of) Makkink evaporation values [mm day-1].

    Notes
    -----

    Meteorological measurements standard at 2 m above soil surface.

    References
    ----------

    H.A.R. de Bruin (1987). From Penman to Makkink, in Hooghart, C. (Ed.),
    Evaporation and Weather, Proceedings and Information. Comm. Hydrological
    Research TNO, The Hague. pp. 5-30.

    Examples
    --------

        >>> Em(21.65,67.0,101300.,24200000.)
        4.503830479197991

    """

    # Test input array/value
    airtemp, rh, airpress, Rs = meteolib._arraytest(airtemp, rh, airpress, Rs)

    # Calculate Delta and gamma constants
    DELTA = meteolib.Delta_calc(airtemp)
    gamma = meteolib.gamma_calc(airtemp, rh, airpress)
    Lambda = meteolib.L_calc(airtemp)

    # calculate Em [mm/day]
    Em = 0.65 * DELTA / (DELTA + gamma) * Rs / Lambda
    return Em


def Ept(
    airtemp=scipy.array([]),
    rh=scipy.array([]),
    airpress=scipy.array([]),
    Rn=scipy.array([]),
    G=scipy.array([]),
):

    """
    Function to calculate daily Priestley - Taylor evaporation:

    .. math::
        E_{pt} = \\alpha \\frac{R_n - G}{\\lambda} \\cdot \\frac{\\Delta}{\\Delta + \\gamma}

    where alpha is set to 1.26.

    Parameters:
        - airtemp: (array of) daily average air temperatures [Celsius].
        - rh: (array of) daily average relative humidity values [%].
        - airpress: (array of) daily average air pressure data [Pa].
        - Rn: (array of) average daily net radiation [J m-2 day-1].
        - G: (array of) average daily soil heat flux [J m-2 day-1].

    Returns:
        - Ept: (array of) Priestley Taylor evaporation values [mm day-1].

    Notes
    -----

    Meteorological parameters normally measured at 2 m above the surface.

    References
    ----------

    Priestley, C.H.B. and R.J. Taylor, 1972. On the assessment of surface
    heat flux and evaporation using large-scale parameters. Mon. Weather
    Rev. 100:81-82.

    Examples
    --------

        >>> Ept(21.65,67.0,101300.,18200000.,600000.)
        6.349456116128078

    """

    # Test input array/value
    airtemp, rh, airpress, Rn, G = meteolib._arraytest(airtemp, rh, airpress, Rn, G)

    # Calculate Delta and gamma constants
    DELTA = meteolib.Delta_calc(airtemp)
    gamma = meteolib.gamma_calc(airtemp, rh, airpress)
    Lambda = meteolib.L_calc(airtemp)
    # calculate Em [mm/day]
    Ept = 1.26 * DELTA / (DELTA + gamma) * (Rn - G) / Lambda
    return Ept


def Epm(
    airtemp=scipy.array([]),
    rh=scipy.array([]),
    airpress=scipy.array([]),
    Rn=scipy.array([]),
    G=scipy.array([]),
    ra=scipy.array([]),
    rs=scipy.array([]),
):

    """
    Function to calculate the Penman Monteith evaporation.

    .. math::
        E_{pm} = \\frac{\\Delta \\cdot (R_n-G)+\\rho \\cdot c_p \\cdot (e_s-e_a)/r_a}{\\lambda \\cdot (\\Delta + \\gamma \\cdot (1+\\frac{r_s}{r_a}))}

    The function can be used with different time intervals, such as commonly
    used hourly or daily time intervals are used. When a plant canopy is wet,
    the surface resistance (rs) becomes zero (stomatal resistance irrelevant,
    as evaporation is directly from wet leaf surface). Function ra() in this
    module can be used to calculate the aerodynamic resistance (ra) from wind
    speed and height parameters.

    Parameters:
        - airtemp: (array of) daily average air temperatures [Celsius].
        - rh: (array of) daily average relative humidity values [%].
        - airpress: (array of) daily average air pressure data [hPa].
        - Rn: (array of) net radiation input over time interval t [J t-1].
        - G: (array of) soil heat flux input over time interval t [J t-1].
        - ra: aerodynamic resistance [s m-1].
        - rs: surface resistance [s m-1].

    Returns:
        - Epm: (array of) Penman Monteith evaporation values [mm t-1].

    References
    ----------

    J.L. Monteith (1965). Evaporation and environment. Symp. Soc. Exp. Biol.
    19: 205-224.

    Examples
    --------

        >>> Epm(21.67,67.0,1013.0,14100000.,500000.,104.,70.)
        3.243341146049407

    """

    # Test input array/value
    airtemp, rh, airpress, Rn, G, ra, rs = meteolib._arraytest(
        airtemp, rh, airpress, Rn, G, ra, rs
    )

    # Calculate Delta, gamma and lambda
    DELTA = meteolib.Delta_calc(airtemp) / 100.0  # [hPa/K]
    airpress = airpress * 100.0  # [Pa]
    gamma = meteolib.gamma_calc(airtemp, rh, airpress) / 100.0  # [hPa/K]
    Lambda = meteolib.L_calc(airtemp)  # [J/kg]
    rho = meteolib.rho_calc(airtemp, rh, airpress)  # [kg m-3]
    cp = meteolib.cp_calc(airtemp, rh, airpress)  # [J kg-1 K-1]
    # Calculate saturated and actual water vapour pressures
    es = meteolib.es_calc(airtemp) / 100.0  # [hPa]
    ea = meteolib.ea_calc(airtemp, rh) / 100.0  # [hPa]
    # Calculate Epm
    Epm = (
        (DELTA * (Rn - G) + rho * cp * (es - ea) / ra)
        / (DELTA + gamma * (1.0 + rs / ra))
    ) / Lambda
    return Epm  # actual ET in mm


def tvardry(
    rho=scipy.array([]),
    cp=scipy.array([]),
    T=scipy.array([]),
    sigma_t=scipy.array([]),
    z=float(),
    d=0.0,
    C1=2.9,
    C2=28.4,
):

    """Function to calculate the sensible heat flux from high
    frequency temperature measurements and their standard deviation:

    .. math::
        H= \\rho c_p \\left(k g (z-d) \\frac{C_2}{C_1^3}\\right)^\\frac{1}{2}\
        \\left( \\frac{\\sigma_T^3}{T}\\right)^\\frac{1}{2}

    Parameters:
        - rho: (array of) air density values [kg m-3].
        - cp: (array of) specific heat at constant temperature values [J kg-1 K-1].
        - T: (array of) temperature data [Celsius].
        - sigma_t: (array of) standard deviation of temperature data [Celsius].
        - z: height [m] above the surface of the temperature measurement.
        - d: displacement height due to vegetation, default set to zero [m].
        - C1: Constant, default set to 2.9 [-] for unstable conditions\
        (de Bruin et al., 1993).
        - C2: Constant, default set to 28.4 [-] for unstable conditions\
        (de Bruin et al., 1993).

    Returns:
        - H: (array of) sensible heat flux [W m-2].

    Notes
    -----
    This function holds only for free convective conditions when C2*z/L >>1,
    where L is the Obhukov length.

    References
    ----------
    - H.A.R. de Bruin and W. Kohsiek and B.J.J.M. van den Hurk (1993). A \
    verification of some methods to determine the fluxes of momentum, sensible \
    heat andwWater vapour using standard seviation and structure parameter of \
    scalar meteorological quantities. Boundary-Layer Meteorology 63(3): 231-257.
    - J.E. Tillman (1972), The indirect determination of stability, heat and\
    momentum fluxes in the atmosphere boundary layer from simple scalar\
    variables during dry unstable conditions, Journal of Applied Meteorology\
    11: 783-792.
    - H.F. Vugts, M.J. Waterloo, F.J. Beekman, K.F.A. Frumau and L.A.\
    Bruijnzeel. The temperature variance method: a powerful tool in the\
    estimation of actual evaporation rates. In J. S. Gladwell, editor,\
    Hydrology of Warm Humid Regions, Proc. of the Yokohama Symp., IAHS\
    Publication No. 216, pages 251-260, July 1993.

    Examples
    --------

        >>> tvardry(1.25,1035.0,25.3,0.25,3.0)
        34.658669290185287
        >>> displ_len=0.25
        >>> tvardry(1.25,1035.0,25.3,0.25,3.0,d=displ_len)
        33.183149497185511
        >>> tvardry(1.25,1035.0,25.3,0.25,3.0,d=displ_len,C2=30)
        34.10507908798597
    """

    # Test input array/value
    rho, cp, T, sigma_t = meteolib._arraytest(rho, cp, T, sigma_t)

    # Define constants
    k = 0.40  # von Karman constant
    g = 9.81  # acceleration due to gravity [m/s^2]
    # C1 =  2.9 # De Bruin et al., 1992
    # C2 = 28.4 # De Bruin et al., 1992
    # L= Obhukov-length [m]

    # Free Convection Limit
    H = rho * cp * scipy.sqrt((sigma_t / C1) ** 3 * k * g * (z - d) / (T + 273.15) * C2)
    # else:
    # including stability correction
    # zoverL = z/L
    # tvardry = rho * cp * scipy.sqrt((sigma_t/C1)**3 * k*g*(z-d) / (T+273.15) *\
    #          (1-C2*z/L)/(-1*z/L))

    # Check if we get complex numbers (square root of negative value) and remove
    # I = find(zoL >= 0 | H.imag != 0);
    # H(I) = scipy.ones(size(I))*NaN;

    return H  # sensible heat flux


def gash79(Pg=scipy.array([]), ER=float, S=float, St=float, p=float, pt=float):

    """
    Function to calculate precipitation interception loss from daily
    precipitation values and vegetation parameters.

    Parameters:
        - Pg: daily rainfall data [mm].
        - ER: evaporation percentage of total rainfall [mm h-1].
        - S: storage capacity canopy [mm].
        - St: stem storage capacity [mm].
        - p: direct throughfall [mm].
        - pt: stem precipitation [mm].

    Returns:
        - Pg: Daily rainfall [mm].
        - Ei: Interception [mm].
        - TF: through fall [mm].
        - SF: stemflow [mm].

    References
    ----------
    J.H.C. Gash, An analytical model of rainfall interception by forests,
    Quarterly Journal of the Royal Meteorological Society, 1979, 105,
    pp. 43-55.

    Examples
    --------
        >>> gash79(12.4,0.15,1.3,0.2,0.2,0.02)
        (12.4, 8.4778854123725971, 0, 3.9221145876274024)
        >>> gash79(60.0,0.15,1.3,0.2,0.2,0.02)
        (60.0, 47.033885412372598, 0, 12.966114587627404)

    """
    # Test input array/value
    Pg = meteolib._arraytest(Pg)

    # Determine length of array Pg
    l = scipy.size(Pg)
    # Check if we have a single precipitation value or an array
    if l < 2:  # Dealing with single value...

        # PGsat calculation (for the saturation of the canopy)
        PGsat = -(1 / ER * S) * scipy.log(1 - (ER / (1 - p - pt)))

        # Set initial values to zero
        Ecan = 0.0
        Etrunk = 0.0

        # Calculate interception for different storm sizes
        if Pg < PGsat and Pg > 0:
            Ecan = (1 - p - pt) * Pg
            if Pg > St / pt:
                Etrunk = St + pt * Pg
            Ei = Ecan + Etrunk
        if Pg > PGsat and Pg < St / pt:
            Ecan = (((1 - p - pt) * PGsat) - S) + (ER * (Pg - PGsat)) + S
            Etrunk = 0.0
            Ei = Ecan + Etrunk
        if Pg > PGsat and Pg > (St / pt):
            Ecan = (
                (((1 - p - pt) * PGsat) - S) + (ER * (Pg - PGsat)) + S + (St + pt * Pg)
            )
            Etrunk = St + pt * Pg
        Ei = Ecan + Etrunk
        TF = Pg - Ei
        SF = 0

    else:
        # Define variables and constants
        n = scipy.size(Pg)
        TF = scipy.zeros(n)
        SF = scipy.zeros(n)
        Ei = scipy.zeros(n)
        Etrunk = scipy.zeros(n)

        # Set results to zero if rainfall Pg is zero
        TF[Pg == 0] = 0.0
        SF[Pg == 0] = 0.0
        Ei[Pg == 0] = 0.0
        Etrunk[Pg == 0] = 0.0

        # PGsat calc (for the saturation of the canopy)
        PGsat = -(1 / ER * S) * scipy.log(1 - (ER / (1 - p - pt)))

        # Process rainfall series
        for i in range(0, n):
            Ecan = 0.0
            Etrunk = 0.0
            if Pg[i] < PGsat and Pg[i] > 0:
                Ecan = (1 - p - pt) * Pg[i]
                if Pg[i] > St / pt:
                    Etrunk = St + pt * Pg[i]
                Ei[i] = Ecan + Etrunk
            if Pg[i] > PGsat and Pg[i] < St / pt:
                Ecan = (((1 - p - pt) * PGsat) - S) + (ER * (Pg[i] - PGsat)) + S
                Etrunk = 0.0
                Ei[i]
            if Pg[i] > PGsat and Pg[i] > (St / pt):
                Ecan = (
                    (((1 - p - pt) * PGsat) - S)
                    + (ER * (Pg[i] - PGsat))
                    + S
                    + (St + pt * Pg[i])
                )
                Etrunk = St + pt * Pg[i]
            Ei[i] = Ecan + Etrunk
            TF[i] = Pg[i] - Ei[i]
    return Pg, TF, SF, Ei


# Run doctest when executing module
if __name__ == "__main__":
    import doctest

    doctest.testmod()
    print("Ran all tests...")
