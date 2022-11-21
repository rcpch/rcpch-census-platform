import requests


def lsoa_for_postcode(postcode):
    postcode = postcode.replace(" ", "")

    url = "https://api.postcodes.io/postcodes/" + postcode
    response = requests.get(url=url)

    if response.status_code == 404:
        print("Could not get LSOA from postcode.")
        return None

    serialised = response.json()
    lsoa = serialised["result"]["codes"]["lsoa"]
    print(serialised["result"])
    return lsoa


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
