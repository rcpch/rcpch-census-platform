import requests
from pprint import pprint


def lsoa_for_postcode(postcode):
    postcode = postcode.replace(" ", "")

    url = "https://api.postcodes.io/postcodes/" + postcode
    response = requests.get(url=url)

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    country = serialised["result"]["country"]
    lsoa = serialised["result"]["codes"]["lsoa"]
    return {"lsoa": lsoa, "country": country}


def regions_for_postcode(postcode):
    postcode = postcode.replace(" ", "")

    url = "https://api.postcodes.io/postcodes/" + postcode
    response = requests.get(url=url)

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    lsoa = serialised["result"]["codes"]["lsoa"]
    return serialised["result"]


def local_authority_district_code_for_postcode(postcode):
    postcode = postcode.replace(" ", "")

    url = "https://api.postcodes.io/postcodes/" + postcode
    response = requests.get(url=url)

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    lad = serialised["result"]["codes"]["admin_district"]
    return lad


def is_valid_postcode(postcode):

    url = f"https://api.postcodes.io/postcodes/{postcode}/validate"
    response = requests.get(url=url)
    if response.status_code == 404:
        print("Postcode validation failure. Could not validate postcode.")
        return False
    else:
        if response.json()["result"] == "True":
            return True
        else:
            return False
