# RCPCH Census Platform

This project is a python 3.11 / Django Rest Framework project providing UK census data, especially Index of Multiple Deprivation as a service.

<p align="center">
    <p align="center">
    <img src='https://github.com/rcpch/rcpch-census-platform/blob/main/static/images/rcpch-logo-mobile.4d5b446caf9a.svg' alt='RCPCH Logo'>
    </p>
</p>

## Why is it needed?

The [Office of National Statistics](https://www.ons.gov.uk) publishes all the Census data exhaustively - this API is not intended to replace it. There is a need though for RCPCH to be able to describe the lived environment and experience of children and young people in a meaningful way, to inform research and clinical practice. This API therefore reports Indices of Deprivation across the devolved nations and in future might produce data/maps at local and regional level for to be consumed by software that RCPCH and others provide.

### UK Areas

The UK can be divided into different areas

1. Output Areas (OAs) - 40-625 households
2. Lower Layer Super Output Areas (LSOAs) - 400-3000 households
3. Middle Layer Super Output Areas (MSOAs) - 2000-15000 households
4. Local Authorities

Each fits within the one below it like a Russian doll.

There are other ways of describing areas across the UK:

1. Ward (electoral)
2. Parishes
3. Local Enterprise Partnerships
4. Parliamentary Constituencies

These do not always fit within the output areas, and boundaries can change.

There is a better explainer [here](https://ocsi.uk/2019/03/18/lsoas-leps-and-lookups-a-beginners-guide-to-statistical-geographies/)

Within healthcare, there are several other important organisational boundaries. These include:

1. Clinical Commissioning Groups (CCGs)
2. Sustainability and Transformation Partnerships (STPs)

### Indices of Multiple Deprivation (IMD)

Indices of Multiple Deprivation (IMDs) are not standardised across the devolved nations. In England and Wales, IMDs are a composite of several domains:

1. income
2. employment
3. education
4. health
5. crime
6. barriers to housing and services
7. living environment

The are subdomains for education (children and young people and adult skills), barriers to housing and services (geographical barriers and wider barriers) and living environment (indoors and outdoors). These domains are then weighted and contribute to the final IMD. Based on the score in each LSOA, LSOAs are then ranked in order, and then split into deciles (with the lower deciles the most deprived). It is important to say that the rankings do not compare between countries - that is a given decile in one country is not the same as the same decile in another. An attempt to do this has been made by [MySociety](https://github.com/mysociety/composite_uk_imd) who have published a Composite UK IMD which brings together all the datasets across the devolved nations. In the process, however, a lot of the detail so whilst this allows the user to compare deprivation scores across countries, [it is not possible to compare the subdomains](https://github.com/mysociety/composite_uk_imd/issues/2). For our purposes, therefore, we will use the individual countries scores, but report these with an appropriate warning.

The process in Scotland is similar, but Data Zones, rather than LSOAs are used, which comprise fewer people. In Northern Ireland, SOAs are used.

## Getting Started

Written in python 3.11 and django-rest-framework, these will need to be installed.

1. clone the repo
2. ```cd rcpch_census_platform```console
3. ```pip install -r requirements/common-requirements.txt```console
4. ```python manage.py createsuperuser --username username --email username@email.com```console
5. ```python manage.py makemigrations```console
6. ```python manage.py migrate```console
7. ```python manage.py seed --mode='add_census_areas'```console

This latter step will take several minutes as it populates the database with all the census and deprivation data.

The final step is to run the server:
```python manage.py runserver```console

If you navigate to ```http://localhost:8000//rcpch-census-platform/api/v1/``` and login, it should be possible then to view the data.

There are 3 routes that accept GET requests:
1. ```/local_authority_districts/```
2. ```/lower_layer_super_output_areas/```
3. ```/indices_of_multiple_deprivation/```
4. ```/boundaries?postcode=```

The IMD route returns IMD data for a given lsoa_code eg:
```http://localhost:8000/rcpch-census-platform/api/v1/indices_of_multiple_deprivation/?lsoa_code=E01003474``` will return:

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
            "imd_score": 4,
            "imd_rank": 32844,
            "imd_decile": 10,
            "income_score": 0,
            "income_score_exponentially_transformed": 0,
            "income_rank": 32822,
            "income_decile": 10,
            "employment_score": 0,
            "employment_score_exponentially_transformed": 0,
            "employment_rank": 32831,
            "employment_decile": 10,
            "education_skills_training_score_exponentially_transformed": 0,
            "education_skills_training_score": 0,
            "education_skills_training_rank": 22206,
            "education_skills_training_decile": 7,
            "children_young_people_sub_domain_score": -2,
            "children_young_people_sub_domain_rank": 32822,
            "children_young_people_sub_domain_decile": 10,
            "adult_skills_sub_domain_score": 0,
            "adult_skills_sub_domain_rank": 32831,
            "adult_skills_sub_domain_decile": 10,
            "health_deprivation_disability_score_exponentially_transformed": 0,
            "health_deprivation_disability_score": -1,
            "health_deprivation_disability_rank": 20783,
            "health_deprivation_disability_decile": 7,
            "crime_score_exponentially_transformed": 12,
            "crime_score": 0,
            "crime_rank": 12993,
            "crime_decile": 4,
            "barriers_to_housing_services_score_exponentially_transformed": 8,
            "barriers_to_housing_services_score": 15,
            "barriers_to_housing_services_rank": 10504,
            "barriers_to_housing_services_decile": 4,
            "geographical_barriers_sub_domain_score": 0,
            "geographical_barriers_sub_domain_rank": 20783,
            "geographical_barriers_sub_domain_decile": 7,
            "wider_barriers_sub_domain_score": 0,
            "wider_barriers_sub_domain_rank": 12993,
            "wider_barriers_sub_domain_decile": 4,
            "living_environment_score": 27,
            "living_environment_score_exponentially_transformed": 25,
            "living_environment_rank": 13739,
            "living_environment_decile": 5,
            "indoors_sub_domain_score": 0,
            "indoors_sub_domain_rank": 13739,
            "indoors_sub_domain_decile": 5,
            "outdoors_sub_domain_score": 0,
            "outdoors_sub_domain_rank": 4948,
            "outdoors_sub_domain_decile": 2,
            "idaci_score": 0,
            "idaci_rank": 32569,
            "idaci_decile": 10,
            "idaopi_score": 0,
            "idaopi_rank": 30751,
            "idaopi_decile": 10,
            "lsoa": "http://localhost:8000/rcpch-census-platform/api/v1/lower_layer_super_output_areas/31392/"
        }
    ]
}
```

Or against a given postcode eg SW1A 1AA (Buckingham Palace):
```http://localhost:8000/rcpch-census-platform/api/v1/indices_of_multiple_deprivation/?postcode=W11AA```

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

There is an additional endpoint: 
```http://localhost:8000/rcpch-census-platform/api/v1/boundaries?postcode=sw1a1aa```

This will return information about a given postcode:

```json
HTTP 200 OK
Allow: GET, HEAD, OPTIONS
Content-Type: application/json
Vary: Accept

{
    "postcode": "SW1A 1AA",
    "quality": 1,
    "eastings": 529090,
    "northings": 179645,
    "country": "England",
    "nhs_ha": "London",
    "longitude": -0.141588,
    "latitude": 51.501009,
    "european_electoral_region": "London",
    "primary_care_trust": "Westminster",
    "region": "London",
    "lsoa": "Westminster 018C",
    "msoa": "Westminster 018",
    "incode": "1AA",
    "outcode": "SW1A",
    "parliamentary_constituency": "Cities of London and Westminster",
    "admin_district": "Westminster",
    "parish": "Westminster, unparished area",
    "admin_county": null,
    "admin_ward": "St. James's",
    "ced": null,
    "ccg": "NHS North West London",
    "nuts": "Westminster",
    "codes": {
        "admin_district": "E09000033",
        "admin_county": "E99999999",
        "admin_ward": "E05013806",
        "parish": "E43000236",
        "parliamentary_constituency": "E14000639",
        "ccg": "E38000256",
        "ccg_id": "W2U3Z",
        "ced": "E99999999",
        "nuts": "TLI32",
        "lsoa": "E01004736",
        "msoa": "E02000977",
        "lau2": "E09000033"
    }
}
```

This information comes directly from the remarkable [postcodes.io](https://postcodes.io) which offers this as a free service. This is a dependency of the RCPCH Census Platform API, since it is used to get LSOAs from a postcode. This process is complicated as boundaries frequently change.
