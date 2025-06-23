"""This module contain functions to convert ra/dec to az/el.

It answers if source is visible now and how long till elevation drops
"""

from statistics import mean

from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time, TimeDelta

# importing the modules
from ska_telmodel.data import TMData

from .common.constant import (
    LOW_LAYOUT_CONSTANT_JSON_FILE_PATH,
    MID_LAYOUT_CONSTANT_JSON_FILE_PATH,
)
from .common.schematic_validation_exceptions import SchematicValidationError


# various functions
def get_mid_telescope_mean_location(tm_data: TMData) -> list:
    """:parm tm_data: telemodel tm data object using which we can load semantic
    validate json.

    :returns: the mean location of mid telescope as a list
    """
    return get_geocentric_mean_location(MID_LAYOUT_CONSTANT_JSON_FILE_PATH, tm_data)


def get_low_telescope_mean_location(tm_data: TMData) -> list:
    """:parm tm_data: telemodel tm data object using which we can load semantic
    validate json.

    :returns: the mean location of low telescope as a list
    """
    return get_geocentric_mean_location(LOW_LAYOUT_CONSTANT_JSON_FILE_PATH, tm_data)


def get_geocentric_mean_location(file_path: str, tm_data: TMData):
    """:parm tm_data: telemodel tm data object using which we can load semantic
    validate json.

    :returns: the mean location of mid telescope as a list :index 0:
        list of geocentric coordinates :index 1: an eq <EarthLocation>
        object :index 2: an eq<GeodeticLocation> object :[[x,y,z]: an eq
        <EarthLocation> object,an eq<GeodeticLocation> object] :parm
        tm_data: telemodel tm data object using which we can load
        semantic validate json.
    """
    tm_data = tm_data[file_path].get_dict()
    mean_x_array = []
    mean_y_array = []
    mean_z_array = []
    for rcpt in tm_data["receptors"]:
        mean_x_array.append(rcpt["location"]["geocentric"]["x"])
        mean_y_array.append(rcpt["location"]["geocentric"]["y"])
        mean_z_array.append(rcpt["location"]["geocentric"]["z"])

    mean_location = [
        [mean(mean_x_array), mean(mean_y_array), mean(mean_z_array)]
    ]  # geocentric coordinates
    obj_geocentric = EarthLocation.from_geocentric(
        x=mean_location[0][0],
        y=mean_location[0][1],
        z=mean_location[0][2],
        unit="m",
    )
    mean_location.append(obj_geocentric)  # the EarthLocation object
    mean_location.append(obj_geocentric.to_geodetic())  # geodetic coordinates
    return mean_location


def ra_dec_to_az_el(
    telesc: str,
    ra: float,
    dec: float,
    obs_time: str,
    el_limit: float,
    tm_data: TMData,
    time_format: str = "iso",
    if_set: bool = False,  # pylint: disable=unused-argument
    time_scale: str = "utc",
    coord_frame: str = "icrs",
    prec: float = 0.0001,
    max_iter: int = 200,
) -> list:
    """
    :returns: the az el in degrees from ra dec at given time
        for the telescopes
        [az el info_isvisible]
    :index 0: azimuth in degrees
    :index 1: elevation in degrees
    :index 2: info_isvisible is True if src visible above/at el_limit
        given time else False
    :param telesc: "mid" for Mid or "low" for Low Telescope
    :param ra: Right ascension in degrees with decimal places
        for arc min,arc sec also covert to degrees.
        Eg 123d30' input 123.5 .
        In case of RA in hh mm sec please also convert to degrees.
    :param dec: Declination in degrees with decimal places.
    :param obs_time: str containing time when source position
        in terms of azimuth, elevation should be calculated.
        Eg '2023-04-18 20:12:18'
    :param time_format: str to choose from available Time.FORMATS.
        Default "iso"
    :param time_scale: str to choose from available Time.SCALES
        Default "utc"
    :param coord_frame: str to choose from available
        Astronomical Coordinate Systems
    :param el_limit: float specifying elevation in degree below which
        our telescope cannot observe the source
    :param prec: float for precision limit
        in degrees to match elevation with given el_limit.
        default: 0.0001 degrees i.e. <1 arcsecond
    :param max_iter: int to specify upto how many iterations can root finder
        use before it stops or reaches required precision. Default is 200.
        Only set higher if suggested by message.
        There is also a seperate message if it is determined
        that root finder is not able to converge starting from given time
    :param tm_data: telemodel tm data object using which
            we can load semantic validate json.

    """
    earth_location = None
    if str.lower(telesc) == "mid":
        earth_location = get_mid_telescope_mean_location(tm_data=tm_data)[1]
    elif str.lower(telesc) == "low":
        earth_location = get_low_telescope_mean_location(tm_data=tm_data)[1]
    else:
        raise SchematicValidationError(message="Invalid telescope name")
    observing_time = Time(obs_time, format=time_format, scale=time_scale)
    coord = SkyCoord(ra, dec, frame=coord_frame, unit="deg")
    az_alt = coord.transform_to(AltAz(location=earth_location, obstime=observing_time))
    az_value = az_alt.az.value  # az value
    alt_value = az_alt.alt.value  # alt value
    az_calculated_Array = [az_value, alt_value]
    # is el above/at el_limit within prec at given time?
    if (alt_value > el_limit) or abs(alt_value - el_limit) < prec:
        az_calculated_Array.append(True)

    az_calculated_Array = __get_info(
        observing_time,
        az_calculated_Array,
        prec,
        max_iter,
        el_limit,
        coord,
        earth_location,
    )

    return az_calculated_Array


def __get_info(
    observing_time, az_alt, prec, max_iter, el_limit, coord, earth_location
) -> list:
    """root finding - when elevation just touched the elevation limit?
    returns az_list or any input list
    after appending list of [info_date_time info_secs_remaining info_msg]"""
    temp_t = observing_time
    temp_t.format = "iso"
    temp_el = az_alt[1]
    list_diff = []
    while max_iter > 0 and abs(temp_el - el_limit) >= prec / 10:
        diff_el = temp_el - el_limit  # 1 deg=240 sec
        temp_t = temp_t + TimeDelta(diff_el * 240, format="sec")
        temp_el = coord.transform_to(AltAz(location=earth_location, obstime=temp_t))
        temp_el = temp_el.alt.value
        list_diff.append(abs(diff_el))
        max_iter = max_iter - 1

    diff = temp_t - observing_time
    diff.format = "sec"
    # checks if err has always decreased monotonically
    # else issues appropriate message
    return az_alt


def ra_degs_from_str_formats(ra_str: str, str_format: int = 1) -> list:
    """Returns a list with the ra in float and error or success message by
    reading from str as given in either of the formats [ra_sum,msg] :param
    ra_str:Right Ascension (one of the celestial coordinates in equatorial
    system) :param str_format:int to give choice for str format.

    1 for hh:mm:ss.ss (default) 2 for dd:mm:ss.ss
    """
    ra_list = ra_str.split(":")
    hh_deg = int(
        ra_list[0]
    )  # first substring is either hh for format 2 or deg for format 1
    min_arcmin = int(ra_list[1])  # second substring
    sec_arcsec = float(ra_list[2])  # third substring
    msg = ""  # storing success or error messages

    ra_sum = hh_deg + min_arcmin / 60 + sec_arcsec / 3600

    if str_format == 1:
        ra_sum = ra_sum * 15  # 1 hr = 15 deg of RA

    return [ra_sum, msg]


def dec_degs_str_formats(dec_str: str) -> list:
    """Returns a list with dec in float and error or success message by reading
    from str :param dec_str:Declination (one of the celestial coordinates in
    equatorial system) in format ±dd:mm:ss.sss."""
    dec_list = dec_str.split(":")
    deg = int(
        dec_list[0]
    )  # first substring is either hh for format 2 or deg for format 1
    arcmin = int(dec_list[1])  # second substring
    arcsec = float(dec_list[2])  # third substring
    msg = ""  # storing success or error messages

    dec_sum = deg + arcmin / 60 + arcsec / 3600
    if deg < 0:
        dec_sum = deg - arcmin / 60 - arcsec / 3600

    return [dec_sum, msg]
