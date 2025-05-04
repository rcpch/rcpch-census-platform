import requests
from django.conf import settings


def lsoa_for_postcode(postcode):
    postcode = postcode.replace(" ", "")
    response = requests.get(
        url=f"{settings.POSTCODES_IO_API_URL}/postcodes/{postcode}",
        headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        timeout=10,  # times out after 10 seconds
    )

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    country = serialised["result"]["country"]
    lsoa = serialised["result"]["codes"]["lsoa"]
    return {"lsoa": lsoa, "country": country}


def regions_for_postcode(postcode):
    postcode = postcode.replace(" ", "")

    response = requests.get(
        url=f"{settings.POSTCODES_IO_API_URL}/postcodes/{postcode}",
        headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        timeout=10,  # times out after 10 seconds
    )

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    lsoa = serialised["result"]["codes"]["lsoa"]
    return serialised["result"]


def local_authority_district_code_for_postcode(postcode):
    postcode = postcode.replace(" ", "")

    response = requests.get(
        url=f"{settings.POSTCODES_IO_API_URL}/postcodes/{postcode}",
        headers={"Ocp-Apim-Subscription-Key": settings.POSTCODES_IO_API_KEY},
        timeout=10,  # times out after 10 seconds
    )

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    lad = serialised["result"]["codes"]["admin_district"]
    return lad
