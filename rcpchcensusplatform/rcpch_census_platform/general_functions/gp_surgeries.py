# python imports
import requests
from requests.exceptions import HTTPError
import os
from typing import Literal


def fetch_all_gp_surgeries(
    country: Literal["england", "wales", "scotland", "northern_ireland"] = "england"
):
    """
    Fetch all surgeries
    """
    url = os.getenv("NHS_ODS_API_URL")

    if country == "england" or country == "wales":
        request_url = f"{url}/organisations?PrimaryRoleId=RO76&Status=Active"
    elif country == "scotland":
        request_url = f"{url}/organisations?PrimaryRoleId=RO227&Status=Active"
    elif country == "northern_ireland":
        request_url = f"{url}/organisations?PrimaryRoleId=RO315&Status=Active"

    try:
        response = requests.get(
            url=request_url,
            timeout=10,  # times out after 10 seconds
        )
        response.raise_for_status()
    except HTTPError as e:
        print(e.response.text)

    return response.json()["Organisations"]
