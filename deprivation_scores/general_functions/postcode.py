from typing import Literal, TypedDict
import requests
from pprint import pprint


def get_postcode_info(postcode: str):
    # Clean
    postcode = postcode.replace(" ", "")

    # Make response
    postcodes_url = f"https://api.postcodes.io/postcodes/{postcode}"
    try:
        response = requests.get(postcodes_url)
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

    # Make response
    terminated_postcodes_url = f"https://api.postcodes.io/terminated_postcodes/{postcode}"
    try:
        response = requests.get(terminated_postcodes_url)
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


def lsoa_for_postcode(postcode):
    data = get_postcode_data(postcode)
    if data["status"] != "success":
        return data
    
    data = data["response"]
    country = data["result"]["country"]
    lsoa = data["result"]["codes"]["lsoa"]
    response = {"lsoa": lsoa, "country": country}
    return {
        "status": "success",
        "response": response,
    }


def regions_for_postcode(postcode):
    data = get_postcode_data(postcode)
    return data


def local_authority_district_code_for_postcode(postcode):
    serialised = get_postcode_data(postcode)
    if serialised["status"] != "success":
        return serialised

    lad = serialised["result"]["codes"]["admin_district"]
    return lad
