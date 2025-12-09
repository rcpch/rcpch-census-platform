# Scripts

Utility scripts for the RCPCH Census Platform.

## scrape_ni_imd.py

Scrapes Northern Ireland Index of Multiple Deprivation (NIMDM 2017) data from the NISRA website for generating test data.

### Requirements

```bash
pip install requests beautifulsoup4
```

### Usage

```bash
python scripts/scrape_ni_imd.py
```

### What it does

1. Iterates through the list of Northern Ireland postcodes defined in `NI_POSTCODES`
2. For each postcode, hits the NISRA deprivation calculator URL:
   `https://deprivation.nisra.gov.uk/MDM/Details?Id={outcode}+{incode}`
3. Extracts from the returned webpage:
   - Postcode (from H1 tag)
   - Table data: SOA name, Urban/Rural classification, Population 2017, Local Government District
   - Deprivation rank (from H3 strong tags, e.g., "rank 137 out of 890")
4. Outputs results in two formats:
   - **Console**: Python dict format ready for copy-pasting into test files
   - **File**: JSON saved to `ni_imd_results.json`

### Output

The script produces a list of dicts with the following structure:

```python
{
    "Postcode": "BT52 1PF",
    "SOA": "Central Coleraine",
    "Urban_Rural": "Urban",
    "Population_2017": "2,175",
    "LGD": "Causeway Coast and Glens",
    "IMD_Rank": 137,
    "Total_SOAs": 890,
}
```

### Customising postcodes

Edit the `NI_POSTCODES` list at the top of the script to change which postcodes are scraped:

```python
NI_POSTCODES = [
    "BT52 1PF",
    "BT28 3WD",
    # Add more postcodes here...
]
```

### Rate limiting

The script includes a 0.5 second delay between requests to be respectful to the NISRA server.

### Notes

- Northern Ireland uses Super Output Areas (SOAs) rather than LSOAs
- The NIMDM 2017 dataset contains 890 SOAs
- Lower rank = higher deprivation (rank 1 is most deprived)
