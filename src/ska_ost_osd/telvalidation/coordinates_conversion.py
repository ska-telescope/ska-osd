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
from .common.error_handling import SchematicValidationError


# various functions
def get_mid_telescope_mean_location(tm_data: TMData) -> list:
    """
    Args:
        tm_data: Telemodel TM data object using which we can load semantic
            validation JSON.

    Returns:
        list: The mean location of the Mid telescope as a list.
    """

    return get_geocentric_mean_location(MID_LAYOUT_CONSTANT_JSON_FILE_PATH, tm_data)


def get_low_telescope_mean_location(tm_data: TMData) -> list:
    """Retrieves the mean location of the Low telescope from the telemodel
    data.

    Args:
        tm_data (TMData): Telemodel TM data object used to load the semantic
            validation JSON.

    Returns:
        list: The mean location of the Low telescope
    """

    return get_geocentric_mean_location(LOW_LAYOUT_CONSTANT_JSON_FILE_PATH, tm_data)


def get_geocentric_mean_location(file_path: str, tm_data: TMData):
    """Retrieves the mean location of the Mid telescope from the provided
    telemodel data.

    Args:
        file_path (str): Path to the `tm_data` file used to
        retrieve the data dictionary.
        tm_data: Telemodel TM data object used to load
        semantic validation JSON.

    Returns:
        list: A list containing:
            - index 0: List of geocentric coordinates [x, y, z].
            - index 1: An `EarthLocation` object representing the location.
            - index 2: A `GeodeticLocation` object representing the location.
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
    """Calculates az el in degrees from ra dec at a given time for the
    specified telescope.

    Returns:
        list: A list containing the following:
            - index 0: Azimuth in degrees.
            - index 1: Elevation in degrees.
            - index 2: `info_isvisible` (bool): True if the source is visible
            (i.e., elevation is above or equal to `el_limit`) at the given time,
            otherwise False.

    Args:
        telesc (str): "mid" for Mid or "low" for Low telescope.
        ra (float): Right Ascension in degrees (e.g., 123.5 for 123d30').
            If provided in hh:mm:ss format, convert to degrees before passing.
        dec (float): Declination in degrees with decimal precision.
        obs_time (str): Observation time as a string when the source position
            (azimuth and elevation) should be calculated.
            Example: '2023-04-18 20:12:18'.
        time_format (str): Format of the observation time. Should be one of
            `astropy.time.Time.FORMATS`. Default is "iso".
        if_set (bool): Boolean value for if_set
        time_scale (str): Time scale of the observation time. Should be one of
            `astropy.time.Time.SCALES`. Default is "utc".
        coord_frame (str): Astronomical coordinate system to be used
            (e.g., "icrs", "fk5", etc.).
        el_limit (float): Elevation limit in degrees. Telescope cannot observe
            below this elevation.
        prec (float): Precision in degrees to match elevation with `el_limit`.
            Default is 0.0001 degrees (i.e., < 1 arcsecond).
        max_iter (int): Maximum number of iterations the root finder can use
            before stopping or reaching the required precision. Default is 200.
            Set higher only if suggested by output messages.
            A separate message is generated if the root finder fails to converge
            from the given starting time.
        tm_data: Telemodel TM data object used to load semantic validation JSON.
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
    """Performs root finding to determine when the elevation just touches the
    specified elevation limit.

    Args:
        observing_time (astropy.time.Time): The initial observing time.
        az_alt (list): A list containing azimuth and elevation values.
        prec (float): Precision threshold for stopping the iteration (in degrees).
        max_iter (int): Maximum number of iterations allowed.
        el_limit (float): Elevation limit to compare against (in degrees).
        coord (astropy.coordinates.SkyCoord): Sky coordinate of the target.
        earth_location (astropy.coordinates.EarthLocation): Location of the observer.

    Returns:
        list: The original `az_alt` list, possibly appended with
        [info_date_time, info_secs_remaining, info_msg]
    """

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
    """Returns a list containing the Right Ascension (RA) in float format and
    an error or success message by parsing the input string. The result is
    returned in the format: [ra_sum, msg].

    Args:
        ra_str (str): Right Ascension (one of the celestial coordinates in the
            equatorial system).
        str_format (int): Integer flag to choose the string format.
            - 1: hh:mm:ss.ss (default)
            - 2: dd:mm:ss.ss

    Returns:
        list: A list containing the parsed RA as a float and either an error
        or success message.
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
    """Returns a list containing the declination in float format and an error
    or success message by parsing the input string.

    Args:
        dec_str (str): Declination (one of the celestial
        coordinates in the equatorial system) in the
        format ±dd:mm:ss.sss.

    Returns:
        list: A list containing the parsed declination
        as a float and either an error or success message.
    """

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
