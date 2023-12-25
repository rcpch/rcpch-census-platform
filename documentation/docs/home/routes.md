---
title: Routes
author: Dr Simon Chapman
---
<!-- The detailed description of the routes should be added to the schema documentation and removed from here -->

There are 10 routes that accept GET requests, all of which return lists that can be filtered, with the exception of ```/indices_of_multiple_deprivation/``` which accepts only a postcode.

1. ```/local_authority_districts/```: params include ```local_authority_district_code```, ```local_authority_district_name```, ```year``` or if none is passed, a list of all local authorities in the UK is returned
2. ```/england_wales_lower_layer_super_output_areas/```: params include ```lsoa_code```, ```lsoa_name```, ```year```. If none is passed, a list of all LSOAs is returned.
3. ```/northern_ireland_small_output_areas/```: params include ```soa_code```, ```soa_name```, ```year```. If none is passed, a list of all SOAs is returned.
4. ```/scotland_datazones/```: params include ```code```,```name```,```year```,```local_authority_code```. If none is passed, a list of all Data Zones is returned.
5. ```/greenspace/```: returns data on green space access by local authority in England, Scotland and Wales
6. ```/english_indices_of_multiple_deprivation/```: params include ```lsoa_code_name``` or ```lsoa_code```, ```local_authority_code``` as well any of the return object fields. It returns a list of all English indices of deprivation
7. ```/welsh_indices_of_multiple_deprivation/```: params include ```lsoa_code```, ```local_authority_code``` as well any of the return object fields. It returns a list of all Welsh indices of deprivation
8. ```/scottish_indices_of_multiple_deprivation/```: params include ```code``` and ```name```, ```local_authority_code``` as well as any of the return object fields. It returns a list of all Scottish indices of deprivation.
9. ```/northern_ireland_indices_of_multiple_deprivation/```: params include ```soa_code``` and ```soa_code_name``` as well as any of the return object fields. It returns a list of all Scottish indices of deprivation
10. ```/indices_of_multiple_deprivation/```: takes a UK postcode (mandatory) and returns deprivation score and quantiles for that LSOA
11. ```/index_of_multiple_deprivation_quantile/```: takes a UK postcode (mandatory) and a requested quantile (mandatory) and returns a deprivation quantile.

example:
SW1A 1AA (Buckingham Palace):
```http://localhost:8000/rcpch-census-platform/api/v1/indices_of_multiple_deprivation/?postcode=SW11AA```

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
        "code": "S01011473",
        "name": "Motherwell South - 03",
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

[![DOI](https://zenodo.org/badge/568991339.svg)](https://zenodo.org/badge/latestdoi/568991339)