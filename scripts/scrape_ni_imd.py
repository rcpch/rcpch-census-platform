#!/usr/bin/env python3
"""
Script to scrape Northern Ireland IMD (NIMDM 2017) data from the NISRA website.
Iterates through postcodes and extracts deprivation data for test generation.
"""

import requests
from bs4 import BeautifulSoup
import time
import json

# Base URL - postcode format is outcode+incode (e.g., BT52+1PF)
BASE_URL = "https://deprivation.nisra.gov.uk/MDM/Details?Id="

# Postcodes to scrape
NI_POSTCODES = [
    "BT52 1PF",
    "BT28 3WD",
    "BT20 5DL",
    "BT7 3FH",
    "BT94 4QD",
    "BT36 4AD",
    "BT51 4PX",
    "BT61 9JT",
    "BT70 1BJ",
    "BT7 3GX",
    "BT80 8WX",
    "BT60 4SS",
    "BT70 3NP",
    "BT38 9NN",
    "BT38 8JN",
    "BT62 2AP",
    "BT70 2ND",
    "BT2 8JL",
    "BT4 3LS",
    "BT70 2HL",
    "BT19 6LS",
    "BT48 7ET",
    "BT5 6QD",
    "BT80 8WX",
    "BT78 5ED",
    "BT71 7SJ",
    "BT74 7JZ",
    "BT25 1AQ",
    "BT71 5BR",
    "BT79 7RT",
    "BT8 7YQ",
    "BT49 0EP",
    "BT67 9AH",
    "BT23 5YH",
    "BT66 6EY",
    "BT35 6LW",
    "BT48 7EE",
    "BT71 5BR",
    "BT19 6DJ",
    "BT52 1DU",
    "BT32 3YJ",
    "BT20 5QW",
    "BT39 9NA",
    "BT26 6QX",
    "BT6 0HG",
    "BT49 0JQ",
    "BT42 2HB",
    "BT13 1FT",
    "BT40 2RX",
    "BT18 0BD",
    "BT70 2TL",
    "BT28 1XJ",
    "BT92 7NJ",
    "BT45 8AA",
    "BT39 0QL",
    "BT28 1JA",
    "BT51 4DR",
    "BT22 2HE",
    "BT78 2RN",
    "BT34 4HL",
    "BT27 4AB",
    "BT61 9PH",
    "BT34 3LF",
    "BT47 3XS",
    "BT39 9TB",
    "BT60 2LU",
    "BT70 1LB",
    "BT45 6LN",
    "BT45 7XQ",
    "BT55 7AE",
    "BT23 6JH",
    "BT44 0PU",
    "BT8 7QN",
    "BT42 1NB",
    "BT25 1LQ",
    "BT71 5AS",
    "BT19 1DT",
    "BT4 3QL",
    "BT34 5UP",
    "BT49 9EY",
    "BT45 7JN",
    "BT51 5AA",
    "BT24 7LX",
    "BT70 2RD",
    "BT47 4HR",
    "BT32 3LA",
    "BT67 0LH",
    "BT62 3PZ",
    "BT40 1TB",
    "BT40 3HQ",
    "BT15 3BU",
    "BT60 2DJ",
    "BT71 5DQ",
    "BT7 1NA",
    "BT6 0JJ",
    "BT71 6DH",
    "BT19 1ZT",
    "BT32 4AS",
    "BT23 4YJ",
    "BT46 5JQ",
    "BT41 3HW",
    "BT74 6AA",
    "BT8 7HY",
    "BT7 1JR",
    "BT51 5PF",
    "BT6 9JS",
    "BT35 6SD",
    "BT7 2HP",
    "BT23 7QB",
    "BT43 5NW",
    "BT37 0ST",
    "BT30 9AJ",
    "BT9 5BN",
    "BT38 7LE",
    "BT80 9HG",
    "BT61 8DL",
    "BT41 1NJ",
    "BT33 0RW",
]


def format_postcode_for_url(postcode: str) -> str:
    """
    Format postcode for URL: 'BT52 1PF' -> 'BT52+1PF'
    """
    parts = postcode.strip().split()
    if len(parts) == 2:
        return f"{parts[0]}+{parts[1]}"
    return postcode.replace(" ", "+")


def scrape_postcode(postcode: str) -> dict | None:
    """
    Scrape IMD data for a single postcode from the NISRA website.

    Returns a dict with:
    - postcode: The postcode from the H1 tag
    - table_data: All data from the table (SOA, Urban/Rural, Population, LGD)
    - deprivation_rank: The rank extracted from h3 strong tags
    """
    url_postcode = format_postcode_for_url(postcode)
    url = f"{BASE_URL}{url_postcode}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching {postcode}: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    result = {
        "query_postcode": postcode,
        "url": url,
    }

    # Extract postcode from H1 tag
    h1 = soup.find("h1")
    if h1:
        result["postcode"] = h1.get_text(strip=True)

    # Extract table data
    table = soup.find("table")
    if table:
        table_data = {}
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                table_data[key] = value
        result["table_data"] = table_data

    # Extract deprivation rank from h3 strong tags
    # Looking for text like "Deprivation Rank - rank 137 out of 890"
    h3_tags = soup.find_all("h3")
    for h3 in h3_tags:
        strong = h3.find("strong")
        if strong:
            text = h3.get_text(strip=True)
            if "rank" in text.lower() or "deprivation" in text.lower():
                result["deprivation_text"] = text
                # Try to extract the rank number
                import re

                match = re.search(
                    r"rank\s*(\d+)\s*out\s*of\s*(\d+)", text, re.IGNORECASE
                )
                if match:
                    result["deprivation_rank"] = int(match.group(1))
                    result["total_soas"] = int(match.group(2))
                break

    # Also look for any strong tags with rank info
    if "deprivation_rank" not in result:
        for strong in soup.find_all("strong"):
            text = strong.get_text(strip=True)
            if "rank" in text.lower():
                import re

                match = re.search(r"rank\s*(\d+)", text, re.IGNORECASE)
                if match:
                    result["deprivation_rank"] = int(match.group(1))
                    break

    return result


def main():
    """Main function to scrape all postcodes."""
    results = []
    failed = []

    print(f"Scraping {len(NI_POSTCODES)} Northern Ireland postcodes...")
    print("=" * 60)

    for i, postcode in enumerate(NI_POSTCODES):
        print(f"[{i+1}/{len(NI_POSTCODES)}] Scraping {postcode}...", end=" ")

        result = scrape_postcode(postcode)

        if result and "deprivation_rank" in result:
            results.append(result)
            print(f"Rank: {result.get('deprivation_rank', 'N/A')}")
        else:
            failed.append(postcode)
            print("FAILED")

        # Be polite to the server
        time.sleep(0.5)

    print("=" * 60)
    print(f"Successfully scraped: {len(results)}")
    print(f"Failed: {len(failed)}")

    if failed:
        print(f"Failed postcodes: {failed}")

    # Output as Python dict for easy copy-paste into tests
    print("\n" + "=" * 60)
    print("RESULTS (copy-paste ready for tests):")
    print("=" * 60)
    print("\nNI_2017_IMD_TEST_DATA = [")
    for r in results:
        table = r.get("table_data", {})
        print("    {")
        print(f'        "Postcode": "{r.get("postcode", r["query_postcode"])}",')
        print(f'        "SOA": "{table.get("Super Output Area (SOA)", "")}",')
        print(
            f'        "Urban_Rural": "{table.get("Urban / Rural Classification", "")}",'
        )
        print(
            f'        "Population_2017": "{table.get("Super Output Area Population 2017", "")}",'
        )
        print(
            f'        "LGD": "{table.get("Local Government District (LGD2014)", "")}",'
        )
        print(f'        "IMD_Rank": {r.get("deprivation_rank", "None")},')
        print(f'        "Total_SOAs": {r.get("total_soas", 890)},')
        print("    },")
    print("]")

    # Also save to JSON file
    output_file = "ni_imd_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nFull results saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
