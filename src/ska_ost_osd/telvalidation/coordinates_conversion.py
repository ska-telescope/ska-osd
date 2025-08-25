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
    """Get the mean location of the Mid telescope.

    :param tm_data: TMData, telemodel TM data object used to load
        semantic validation JSON.
    :return: list, the mean location of the Mid telescope.
    """

    return get_geocentric_mean_location(MID_LAYOUT_CONSTANT_JSON_FILE_PATH, tm_data)


def get_low_telescope_mean_location(tm_data: TMData) -> list:
    """Retrieve the mean location of the Low telescope.

    :param tm_data: TMData, telemodel TM data object used to load
        semantic validation JSON.
    :return: list, the mean location of the Low telescope.
    """

    return get_geocentric_mean_location(LOW_LAYOUT_CONSTANT_JSON_FILE_PATH, tm_data)


def get_geocentric_mean_location(file_path: str, tm_data: TMData):
    """Retrieve the mean location of the telescope from telemodel data.

    :param file_path: str, path to the tm_data file used to retrieve the
    data dictionary.
    :param tm_data: TMData, telemodel TM data object used to load semantic
    validation JSON.
    :return: list, containing:
        - index 0: list of geocentric coordinates [x, y, z].
        - index 1: EarthLocation object representing the location.
        - index 2: GeodeticLocation object representing the location.
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
    """Calculate azimuth and elevation in degrees from RA and Dec at a given
    time for a specified telescope.

    :param telesc: str, "mid" for Mid or "low" for Low telescope.
    :param ra: float, Right Ascension in degrees (convert from hh:mm:ss if needed).
    :param dec: float, Declination in degrees.
    :param obs_time: str, observation time (e.g., '2023-04-18 20:12:18').
    :param el_limit: float, elevation limit in degrees; telescope cannot
     observe below this.
    :param tm_data: TMData, telemodel TM data object used to load semantic
     validation JSON.
    :param time_format: str, format of observation time, default "iso".
    :param if_set: bool, optional boolean flag (default False).
    :param time_scale: str, time scale of observation time, default "utc".
    :param coord_frame: str, astronomical coordinate system (e.g., "icrs", "fk5").
    :param prec: float, precision in degrees for elevation matching, default 0.0001.
    :param max_iter: int, max iterations for root finder, default 200.
    :return: list containing:
     - index 0: azimuth in degrees,
     - index 1: elevation in degrees,
     - index 2: info_isvisible (bool), True if elevation ≥ el_limit, else False.
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
    """Perform root finding to determine when elevation just touches the
    specified limit.

    :param observing_time: astropy.time.Time, initial observing time.
    :param az_alt: list, azimuth and elevation values.
    :param prec: float, precision threshold in degrees for stopping
        iteration.
    :param max_iter: int, maximum allowed iterations.
    :param el_limit: float, elevation limit in degrees.
    :param coord: astropy.coordinates.SkyCoord, sky coordinate of the
        target.
    :param earth_location: astropy.coordinates.EarthLocation, observer
        location.
    :return: list, original az_alt list, possibly appended with
        [info_date_time, info_secs_remaining, info_msg].
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
    """Parse Right Ascension (RA) string and return RA in degrees with status
    message.

    :param ra_str: str, Right Ascension string (e.g., "hh:mm:ss.ss" or "dd:mm:ss.ss").
    :param str_format: int, string format flag:
        - 1: hh:mm:ss.ss (default)
        - 2: dd:mm:ss.ss
    :return: list, [RA in degrees as float, message string].
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
    """Parse declination string and return declination in degrees with status
    message.

    :param dec_str: str, Declination string in format ±dd:mm:ss.sss.
    :return: list, [declination in degrees as float, message string].
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
