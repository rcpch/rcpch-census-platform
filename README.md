# RCPCH Census Platform

This project is a python 3.11 / Django Rest Framework project providing UK census data, especially Index of Multiple Deprivation as a service.

<p align="center">
     <img src='https://raw.githubusercontent.com/rcpch/rcpch-census-platform/refs/heads/live/static/images/rcpch-logo-mobile.4d5b446caf9a.svg' alt='RCPCH Logo'>
</p>

<!--
Documentation routing note for humans and LLMs:
- README is intentionally overview-first and avoids operational/detail duplication.
- Human/operator runbooks live in site/docs/.
- Agent/LLM-specific operational constraints live in AGENTS.md.
-->

## Documentation Routing (Humans and LLMs)

Use this file as a high-level entry point.

- For boundary datasets, tile table contracts, and geometry processing details, use [site/docs/boundaries.md](site/docs/boundaries.md).
- For managed database restore and seeding operations, use [site/docs/managed-database-seeding.md](site/docs/managed-database-seeding.md).
- For deployment flow and architecture, use [site/docs/deploy.md](site/docs/deploy.md).
- For coding-agent and LLM operational constraints, use [AGENTS.md](AGENTS.md).

If README content conflicts with site/docs, treat site/docs as the source of truth.


## Why is it needed?

The [Office of National Statistics](https://www.ons.gov.uk) publishes all the Census data exhaustively - this project is not intended to replace it. There is a need though for RCPCH to be able to describe the lived environment and experience of children and young people in a meaningful way, to inform research, audit and clinical practice. The project will curate social and environmental data where they have impact on children's health or on paediatrics, available to clinicians and researchers. It is a work in progress. The first application within this project is an API to address deprivation, by reporting indices of multiple deprivation from across the UK against a postcode. It is consumed by software that RCPCH provide. It supports the latest deprivation score publications including 2025.

The second feature of this project is to serve the shape files - the boundaries of the LSOAs, SOAs and Data Zones - as tiles coloured by IMD.

### UK Areas

The UK can be divided into different areas

1. Output Areas (OAs) - 40-625 households
2. Lower Layer Super Output Areas (LSOAs) - 400-3000 households
3. Middle Layer Super Output Areas (MSOAs) - 2000-15000 households
4. Local Authorities

Each fits within the one below it like a Russian doll.

There are other ways of describing areas across the UK:

1. Wards (electoral)
2. Parishes
3. Local Enterprise Partnerships
4. Parliamentary Constituencies

These do not always fit within the output areas, and boundaries can change.

There is a better explainer [here](https://ocsi.uk/2019/03/18/lsoas-leps-and-lookups-a-beginners-guide-to-statistical-geographies/)

Within this repository, on 2011 LSOA boundaries and identifiers are included, as well as 2019 Local Authorities. There are more recent 2021 LSOA boundaries, but there are no indices of multiple deprivation associated with these.

Within healthcare, there are several other important organisational boundaries.

Integrated Care Boards were introduced on 1st July 2022, taking over from Sustainability and Transformation Partnerships (STPs) and 106 Clinical Commissioning Groups (CCGs) as the top-level organisational units for planning and commissioning health and social care. Commissioning now is controlled by the 42 ICBs (and ICPs or integrated care partnerships). Other hierarchies include providers (such as NHS Trusts, Mental Health Trusts, GP surgeries, pharmacies, ambulance services etc) and Primary Care Networks (PCNs).

### Indices of Multiple Deprivation (IMD)

Indices of Multiple Deprivation (IMDs) are not standardised across the devolved nations. They are specific to each country and are derived from census data. The methodology for the calculation though is essentially the same. It involves breaking the country up into units comparable by population size - in England and Wales, this is LSOAs, in Scotland it is Data Zones and in Northern Ireland it is SOAs. Each unit then is allocated a score to summarise certain deprivation domains. These vary across the 4 countries: 

| England                          | Wales                 | Scotland          | Northern Ireland                  |
|:---------------------------------|:----------------------|:------------------|:----------------------------------|
| income                           | income                | income            | income                            |
| employment                       | employment            | employment        | employment                        |
| education                        | health                | education         | health deprivation and disability |
| health                           | education             | health            | education skills and training     |
| crime                            | access to services    | access            | access to services                |
| barriers to housing and services | housing               | crime             | living environment                |
| living environment               | community safety      | housing           | crime and disorder                |
|                                  | physical environment  |                   |                                   |
| *32844 LSOAs (2019 data)*                    | *1909 LSOAs (2019 data)*          | *6976 Data Zones (2020 data)* | *890 SOAs (2017 data)*                        |
| *33755 LSOAs (2021 data)*                    | *1917 LSOAs (2021 data)*          |  |                         |

In England, there are also subdomains for education (children and young people and adult skills), barriers to housing and services (geographical barriers and wider barriers) and living environment (indoors and outdoors).

These domains are then weighted and contribute to the final index of multiple deprivation score. Based on the score in each LSOA, LSOAs are then ranked by deprivation score, and then split into quantiles (with the lower quantiles the most deprived). It is important to say that the rankings do not compare between countries - that is a given decile in one country is not the same as the same decile in another, and this is because the scores are not standardised across the UK, only across each nation. An attempt to do this has been made by [MySociety](https://github.com/mysociety/composite_uk_imd) who have published a Composite UK IMD which brings together all the datasets across the devolved nations. In the process, however, a lot of the detail is lost so whilst this allows the user to compare deprivation scores across countries, [it is not possible to compare the subdomains](https://github.com/mysociety/composite_uk_imd/issues/2). For our purposes, therefore, we will use the individual countries scores, but report these with an appropriate warning.

### Datasets

| Country | Denomination | Year | Count | Reference |
|:--------|:-------------|:-----|------:|:----------|
| England | LSOA | 2011 | 32,844 | |
| England | LSOA | 2021 | 33,755 | |
| Wales | LSOA | 2011 | 1,909 | |
| Wales | LSOA | 2021 | 1,917 | |
| Scotland | Data Zone | 2011 | 6,976 | |
| Northern Ireland | SOA | 2001 | 890 | |
| England | Local Authority District | 2019 | 317 | |
| England | Local Authority District | 2024 | 296 | |
| Wales | Local Authority District | 2019 | 22 | |
| Wales | Local Authority District | 2024 | 22 | |
| Scotland | Local Authority | 2011 | 32 | |
| England | Ward | 2019 | 7,180 | |
| England | Ward | 2024 | 7,461 | |
| Wales | Ward | 2019 | 852 | |
| Wales | Ward | 2024 | 881 | |
| England | MSOA | 2011 | 6,791 | |
| England | MSOA | 2021 | 6,856 | |
| Wales | MSOA | 2011 | 410 | |
| Wales | MSOA | 2021 | 416 | |
| England | IMD | 2019 | 32,844 | |
| England | IMD | 2025 | 33,755 | |
| Wales | WIMD | 2019 | 1,909 | |
| Scotland | SIMD | 2020 | 6,976 | |
| Northern Ireland | NIMDM | 2017 | 890 | |
| England, Wales, Scotland | Green Space | 2020 | 371 | |
| England | Population Density | 2024 | 32,844 | |

#### IMD Boundary Summary

| Country | IMD Version | IMD Year | Small Area | Small Area Year | Local Authority | LA Year |
|:--------|:------------|:---------|:-----------|:----------------|:----------------|:--------|
| England | IoD | 2019 | LSOA | 2011 | LAD | 2019 |
| England | IoD | 2025 | LSOA | 2021 | LAD | 2024 |
| Wales | WIMD | 2019 | LSOA | 2011 | LAD | 2019 |
| Scotland | SIMD | 2020 | Data Zone | 2011 | LA | 2011 |
| Northern Ireland | NIMDM | 2017 | SOA | 2001 | - | - |

## Getting Started

Written in python 3.11 and django-rest-framework. We recommend using `pyenv` or similar python version manager and virtual environment manager.

### Option One (Quick Local Setup)

1. clone the repo
2. ```cd rcpch_census_platform```
3. ```pip install -r requirements/common-requirements.txt```
4. ```python manage.py createsuperuser --username username --email username@email.com```
5. ```python manage.py makemigrations```
6. ```python manage.py migrate```
7. `python manage.py seed --mode='__all__'`
8. `python manage.py seed --mode='import_bfc_boundaries'`

Notes:

- `import_bfc_boundaries` can take significant time on a fresh build.
- For seeding modes, boundary import behavior, and validation semantics, use [site/docs/boundaries.md](site/docs/boundaries.md).

The final step is to run the server:
`python manage.py runserver`

## Tests — postcode mocking

By default the test suite uses mocked responses for the external postcodes.io API so tests are fast and deterministic.

- Default behavior: tests use the mock data in `tests/postcode_mock_data.py` (no environment variables required).
- To run tests against the real postcodes.io API set the environment variable `REAL_POSTCODES_IO=1` or annotate a test with `@pytest.mark.real_postcodes_io`.
- CI runs the seeding step and executes the full test-suite; mocking is enabled by default in the test runner, so CI will use the mocks unless overridden.

If you need to regenerate the mocked responses, run `python scripts/capture_postcode_responses.py` and update `tests/postcode_mock_data.py`.

To run the tests using the real postcodes API:

`REAL_POSTCODES_IO=1 pytest -q`

To run the tests without:

`pytest -q`

### Docker Compose development install

This repository includes a Docker Compose development stack with:

- `web`: Django/DRF API (runs on port `8000`)
- `db`: PostGIS (runs on port `5432`)
- `pg_tileserv`: vector tile server backed by PostGIS (runs on port `7800`)

Prerequisites:

- Docker Desktop (or Docker Engine + Compose)

Steps:

1. Clone the repo
2. From the repository root, start the dev stack:
    - `./s/dev`
    - (equivalent: `docker compose -f docker-compose-postgis.yml up --build`)
3. The `web` container will wait for the database, run `collectstatic`, run `migrate`, and then start Django.
4. Seed the database:
    - `docker compose -f docker-compose-postgis.yml exec web python manage.py seed --mode='__all__'`
    - Then: `docker compose -f docker-compose-postgis.yml exec web python manage.py seed --mode='import_bfc_boundaries'`

For full seeding guidance (including partial geometry rebuild behavior and validation modes), use [site/docs/boundaries.md](site/docs/boundaries.md).

Useful URLs:

- API: `http://localhost:8000/rcpch-census-platform/api/v1/`
- Tileserver (pg_tileserv): `http://localhost:7800/`

Note: the nginx reverse-proxy container is used in the Azure Container Apps deployment to route `/tiles/*` and the API under a single public ingress. For local development you can usually hit Django (`:8000`) and pg_tileserv (`:7800`) directly.

### Demo map site (GitHub Pages + local dev)

The MapLibre demo lives in the `site/` folder and is deployed to GitHub Pages via a GitHub Actions workflow.

For local development, you can preview it in VS Code:

1. Open `site/index.html`
2. Right click the file in the Explorer and choose **Open with Live Server** (requires the Live Server extension)

When the demo is served from `localhost` / `127.0.0.1`, it will default to using local tiles at `http://localhost:7800`.
To point it at a deployed tiles endpoint, pass a query parameter:

- `?tilesBase=https://<your-host>/tiles`

### Seeding and Validation Commands

Useful commands:

- `python manage.py seed --mode test_table_totals`
- `python manage.py seed --mode test_geometries`

For expected counts, boundary tier validation behavior, and operational interpretation of these checks, use [site/docs/boundaries.md](site/docs/boundaries.md).

<!-- TODO: #14 #13 remove all references to auth, logins, or tokens in the census engine readme -->

## Creating openapi.yml and openapi.json files

rf-spectacular can create the openapi3 spec files for you using the following command.

We only really use the JSON version, but it's easy to create a YAML equivalent if needed also.

JSON
```shell
docker compose -f docker-compose.dev-init.yml exec web python manage.py spectacular --file openapi.json
```
YAML
```shell
docker compose -f docker-compose.dev-init.yml exec web python manage.py spectacular --file openapi.json
```

The full list of endpoints can be viewed in the openAPI spec above, but the key endpoints that are important are: 

1.  ```/indices_of_multiple_deprivation/```: takes a UK postcode (mandatory) and returns deprivation score and quantiles for that LSOA. It optionally accepts a year for the request IMD dataset, defaulting to 2019 for England and Wales, 2020 for Scotland and 2017 for Northern Ireland
2.  ```/index_of_multiple_deprivation_quantile/```: takes a UK postcode (mandatory) and a requested quantile (mandatory) and returns a deprivation quantile. Also accepts a  year as above.

example:
SW1A 1AA (Buckingham Palace):
```http://localhost:8000/rcpch-census-platform/api/v1/indices_of_multiple_deprivation/?postcode=SW1A1AA```

```json
HTTP 200 OK
Allow: GET, POST, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "imd_score": 9,
            "imd_rank": 28230,
            "imd_decile": 9,
            "income_score": 0,
            "income_score_exponentially_transformed": 0,
            "income_rank": 22807,
            "income_decile": 7,
            "employment_score": 0,
            "employment_score_exponentially_transformed": 0,
            "employment_rank": 32492,
            "employment_decile": 10,
            "education_skills_training_score_exponentially_transformed": 3,
            "education_skills_training_score": 4,
            "education_skills_training_rank": 17078,
            "education_skills_training_decile": 6,
            "children_young_people_sub_domain_score": 0,
            "children_young_people_sub_domain_rank": 22807,
            "children_young_people_sub_domain_decile": 7,
            "adult_skills_sub_domain_score": 0,
            "adult_skills_sub_domain_rank": 32492,
            "adult_skills_sub_domain_decile": 10,
            "health_deprivation_disability_score_exponentially_transformed": 0,
            "health_deprivation_disability_score": -2,
            "health_deprivation_disability_rank": 28829,
            "health_deprivation_disability_decile": 9,
            "crime_score_exponentially_transformed": 15,
            "crime_score": 0,
            "crime_rank": 6428,
            "crime_decile": 2,
            "barriers_to_housing_services_score_exponentially_transformed": 14,
            "barriers_to_housing_services_score": 19,
            "barriers_to_housing_services_rank": 1239,
            "barriers_to_housing_services_decile": 1,
            "geographical_barriers_sub_domain_score": 0,
            "geographical_barriers_sub_domain_rank": 28829,
            "geographical_barriers_sub_domain_decile": 9,
            "wider_barriers_sub_domain_score": 2,
            "wider_barriers_sub_domain_rank": 6428,
            "wider_barriers_sub_domain_decile": 2,
            "living_environment_score": 54,
            "living_environment_score_exponentially_transformed": 68,
            "living_environment_rank": 7273,
            "living_environment_decile": 3,
            "indoors_sub_domain_score": 0,
            "indoors_sub_domain_rank": 7273,
            "indoors_sub_domain_decile": 3,
            "outdoors_sub_domain_score": 2,
            "outdoors_sub_domain_rank": 76,
            "outdoors_sub_domain_decile": 1,
            "idaci_score": 0,
            "idaci_rank": 32297,
            "idaci_decile": 10,
            "idaopi_score": 0,
            "idaopi_rank": 32722,
            "idaopi_decile": 10,
            "lsoa": "http://localhost:8000/rcpch-census-platform/api/v1/lower_layer_super_output_areas/32961/"
        }
    ]
}
```

Note that this endpoint accepts any postcode from across the UK, and returns a slightly different response object depending on the country. Examples of England are above.

Wales is as follows (```rcpch-census-engine.azurewebsites.net/api/v1/indices_of_multiple_deprivation?postcode=CF14 3LX```):

```json
{
    "id": 1712,
    "imd_rank": 1362,
    "imd_quartile": 3,
    "imd_quintile": 4,
    "imd_decile": 8,
    "imd_score": "11.5",
    "income_rank": 1576,
    "income_quartile": 4,
    "income_quintile": 5,
    "income_decile": 9,
    "income_score": "4.4",
    "employment_rank": 1865,
    "employment_quartile": 4,
    "employment_quintile": 5,
    "employment_decile": 10,
    "employment_score": "0.5",
    "health_rank": 1476,
    "health_quartile": 4,
    "health_quintile": 4,
    "health_decile": 8,
    "health_score": "5.8",
    "education_rank": 1559,
    "education_quartile": 4,
    "education_quintile": 5,
    "education_decile": 9,
    "education_score": "4.6",
    "access_to_services_rank": 1675,
    "access_to_services_quartile": 4,
    "access_to_services_quintile": 5,
    "access_to_services_decile": 9,
    "access_to_services_score": "3.0",
    "housing_rank": 72,
    "housing_quartile": 1,
    "housing_quintile": 1,
    "housing_decile": 1,
    "housing_score": "69.1",
    "community_safety_rank": 1314,
    "community_safety_quartile": 3,
    "community_safety_quintile": 4,
    "community_safety_decile": 7,
    "community_safety_score": "8.5",
    "physical_environment_rank": 78,
    "physical_environment_quartile": 1,
    "physical_environment_quintile": 1,
    "physical_environment_decile": 1,
    "physical_environment_score": "67.7",
    "year": 2019,
    "lsoa": 33860
}
```

Scotland (```rcpch-census-engine.azurewebsites.net/api/v1/indices_of_multiple_deprivation?postcode=ML1 1AA```):

```json
{
    "id": 4968,
    "year": 2020,
    "version": 2,
    "imd_rank": 192,
    "income_rank": 440,
    "employment_rank": 121,
    "education_rank": 354,
    "health_rank": 138,
    "access_rank": 5390,
    "crime_rank": 32,
    "housing_rank": 3076,
    "data_zone": {
        "id": 4968,
        "data_zone_code": "S01011473",
        "data_zone_name": "Motherwell South - 03",
        "year": 2011,
        "local_authority": 361
    }
}
```

and Northern Ireland (```rcpch-census-engine.azurewebsites.net/api/v1/indices_of_multiple_deprivation?postcode=BT2 7DX```):

```json
{
    "id": 272,
    "imd_rank": 163,
    "year": 2017,
    "income_rank": 464,
    "employment_rank": 128,
    "health_deprivation_and_disability_rank": 70,
    "education_skills_and_training_rank": 104,
    "access_to_services_rank": 739,
    "living_environment_rank": 187,
    "crime_and_disorder_rank": 123,
    "soa": {
        "id": 272,
        "year": 2001,
        "soa_code": "95GG39S1",
        "soa_name": "Shaftesbury_1"
    }
}
```

The endpoint for deprivation quantile: It accepts a postcode and a quantile_type, one of [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]

```
{{base_url}}/index_of_multiple_deprivation_quantile?quantile=5&postcode=SY10 0AA
```

returns:

```json
{
    "result": {
        "rank": 1038,
        "requested_quantile": 5,
        "requested_quantile_name": "quintile",
        "data_quantile": 3,
        "country": "wales",
        "error": null
    }
}
```

**ACKNOWLEDGEMENT**
The postcode look up is powered by an RCPCH hosted instance of [postcodes.io](api.postcodes.io)

[![DOI](https://zenodo.org/badge/568991339.svg)](https://zenodo.org/badge/latestdoi/568991339)
