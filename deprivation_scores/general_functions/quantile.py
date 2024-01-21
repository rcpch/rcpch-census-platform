from typing import Literal
import math


def quantile_for_rank(
    rank,
    requested_quantile=Literal[2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20],
    country=Literal["england", "scotland", "wales", "northern_ireland"],
):
    """
    Returns a quantile against a rank
    Params
    rank: decimal - usually an int but some ranks in scotland can be decimals if LSOAs have no data
    quantile: int must be less than/equal to 20, corresponding to one of [2,3,4,5,6,7,8,10,12,18,20]:
    country: str must be one of ['england', 'scotland', 'wales', 'northern_ireland']
    """

    QUANTILES = {
        2: "median",
        3: "tertile",
        4: "quartile",
        5: "quintile",
        6: "sextile",
        7: "septile",
        8: "octile",
        10: "decile",
        12: "duodecile",
        18: "hexadecile",
        20: "vigintile",
    }

    if int(requested_quantile) not in QUANTILES.keys():
        return {
            "rank": None,
            "requested_quantile": requested_quantile,
            "requested_quantile_name": None,
            "data_quantile": None,
            "country": country,
            "error": f"{requested_quantile} is not a valid quantile.",
        }

    english_rank_total = 32844
    welsh_rank_total = 1909
    scottish_rank_total = 6976
    northern_ireland_total = 890

    country_rank = 0
    if country == "england":
        country_rank = english_rank_total
    elif country == "wales":
        country_rank = welsh_rank_total
    elif country == "scotland":
        country_rank = scottish_rank_total
    elif country == "northern_ireland":
        country_rank = northern_ireland_total
    else:
        raise ValueError("No country supplied")

    quantile_limit = country_rank / int(requested_quantile)

    return {
        "rank": rank,
        "requested_quantile": int(requested_quantile),
        "requested_quantile_name": QUANTILES.get(int(requested_quantile)),
        "data_quantile": math.floor(rank / quantile_limit) + 1,
        "country": country,
        "error": None,
    }
