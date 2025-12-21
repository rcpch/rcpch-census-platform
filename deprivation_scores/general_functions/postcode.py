from typing import Literal, TypedDict
import requests
from django.conf import settings


def get_postcode_info(postcode: str):
    # Clean
    postcode = postcode.replace(" ", "")

    try:
        response = requests.get(
            url=f"{settings.POSTCODES_IO_API_URL}/postcodes/{postcode}",
            headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP ERROR: {err}")
    except Exception as err:
        print(f"Other error occurred: {err}")

    return None


def get_terminated_postcode_info(postcode: str):
    # Clean
    postcode = postcode.replace(" ", "")

    try:
        response = requests.get(
            url=f"{settings.POSTCODES_IO_API_URL}/terminated_postcodes/{postcode}",
            headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        )
        response.raise_for_status()
        print(f"Terminated postcode found: {postcode}")
        return response.json()
    except requests.exceptions.HTTPError as err:
        print(f"HTTP ERROR: {err}")
    except Exception as err:
        print(f"Other error occurred: {err}")

    return None


class LSOAPostcodeObject(TypedDict):
    status: Literal["success", "error", "terminated_postcode"]
    response: dict | str


def get_postcode_data(postcode: str) -> dict:
    if not (data := get_postcode_info(postcode)):
        # Try terminated postcode endpoint
        print("Trying terminated postcode url...")
        if not (terminated_postcode_info := get_terminated_postcode_info(postcode)):
            return {
                "status": "error",
                "response": "Could not get LSOA from postcode.",
            }
        print(f"Terminated postcode info: {terminated_postcode_info}")
        return {
            "status": "terminated_postcode",
            "response": terminated_postcode_info.get("result"),
        }
    return {
        "status": "success",
        "response": data,
    }


def lsoa_for_postcode(postcode, year=2011):
    data = get_postcode_data(postcode)
    if data["status"] != "success":
        return data

    data = data["response"]
    country = data["result"]["country"]
    if country == "Northern Ireland":
        lsoa = data["result"]["codes"][
            "lsoa11"
        ]  # this returns the 2011 Super Output Area for NI
    elif country == "Scotland":
        lsoa = data["result"]["codes"][
            "lsoa11"
        ]  # this returns the 2011 Data Zone for Scotland
    else:  # England or Wales
        if year == 2021:
            lsoa = data["result"]["codes"]["lsoa21"]
        else:  # year == 2011 for England and Wales
            lsoa = data["result"]["codes"]["lsoa11"]
    response = {"lsoa": lsoa, "country": country}
    return {
        "status": "success",
        "response": response,
    }


def regions_for_postcode(postcode):
    data = get_postcode_data(postcode)
    return data
