from typing import Literal, TypedDict
import requests
from django.conf import settings
import logging
from urllib.parse import quote


logger = logging.getLogger(__name__)


def get_postcode_info(postcode: str):
    # Clean
    postcode = postcode.replace(" ", "")

    try:
        response = requests.get(
            # quote() stops user-supplied input from altering the path or query
            # string of the outbound postcodes.io request
            url=f"{settings.POSTCODES_IO_API_URL}/postcodes/{quote(postcode, safe='')}",
            headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP ERROR: {err}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")

    return None


def get_terminated_postcode_info(postcode: str):
    # Clean
    postcode = postcode.replace(" ", "")

    try:
        response = requests.get(
            url=f"{settings.POSTCODES_IO_API_URL}/terminated_postcodes/{quote(postcode, safe='')}",
            headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        )
        response.raise_for_status()
        print(f"Terminated postcode found: {postcode}")
        return response.json()
    except requests.exceptions.HTTPError as err:
        logger.error(f"HTTP ERROR: {err}")
    except Exception as err:
        logger.error(f"Other error occurred: {err}")

    return None


class LSOAPostcodeObject(TypedDict):
    status: Literal["success", "error", "terminated_postcode"]
    response: dict | str


def get_postcode_data(postcode: str) -> dict:
    if not (data := get_postcode_info(postcode)):
        # Try terminated postcode endpoint
        logger.info("Trying terminated postcode url...")
        if not (terminated_postcode_info := get_terminated_postcode_info(postcode)):
            return {
                "status": "error",
                "response": "Could not get LSOA from postcode.",
            }
        logger.info(f"Terminated postcode info: {terminated_postcode_info}")
        return {
            "status": "terminated_postcode",
            "response": terminated_postcode_info.get("result"),
        }
    return {
        "status": "success",
        "response": data,
    }


def lsoa_for_postcode(postcode, lsoa_year=None):
    """
    Returns LSOA/SOA/Data Zone for a given postcode
    If country is England or Wales, returns LSOA for specified year (2011 or 2021)
    If country is Scotland, returns Data Zone (2011)
    If country is Northern Ireland, returns SOA (2011)

    :param postcode: Description
    :param lsoa_year: Description
    """
    # UK postcodes are at most 8 characters including the space; reject
    # anything longer before it reaches the outbound lookup or the logs
    if len(postcode) > 20:
        logger.warning("Over-long postcode rejected (%d chars supplied)", len(postcode))
        return {
            "status": "error",
            "response": "Invalid postcode supplied.",
        }
    try:
        data = get_postcode_data(postcode)
    except Exception as e:
        logger.error(f"Error getting postcode data: {e}")
        return {
            "status": "error",
            "response": "Could not get LSOA from postcode.",
        }
    if data["status"] != "success":
        logger.error(f"Error getting postcode data: {data}")
        return data

    data = data["response"]
    country = data["result"]["country"]
    codes = data["result"]["codes"]
    lsoa11_code = codes["lsoa11"]
    # postcodes.io supplies both vintages for England and Wales; fall back to
    # the 2011 code where a 2021 code is not published
    lsoa21_code = codes.get("lsoa21") or lsoa11_code
    if country == "Northern Ireland":
        lsoa = lsoa11_code  # this returns the 2001 Super Output Area for NI (though labelled lsoa11)
        lsoa_year = 2001
    elif country == "Scotland":
        lsoa = lsoa11_code  # this returns the 2011 Data Zone for Scotland
        lsoa_year = 2011
    else:  # England or Wales
        if lsoa_year == 2021:
            lsoa = lsoa21_code
            lsoa_year = 2021
        else:  # year == 2011 for England and Wales
            lsoa = lsoa11_code
            lsoa_year = 2011
    response = {
        "lsoa": lsoa,
        "country": country,
        "lsoa_year": lsoa_year,
        # both boundary vintages, so callers can pick the dataset year after
        # the country is known (e.g. year=latest)
        "lsoa11": lsoa11_code,
        "lsoa21": lsoa21_code,
    }
    return {
        "status": "success",
        "response": response,
    }


def regions_for_postcode(postcode):
    data = get_postcode_data(postcode)
    return data
