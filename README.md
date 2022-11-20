# RCPCH Census Platform

This project is a python 3.11 / Django Rest Framework project providing UK census data, especially Index of Multiple Deprivation as a service.

## UK Areas

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

## Indices of Multiple Deprivation

Indices of Multiple Deprivation (IMDs) are not standardised across the devolved nations. In England and Wales, IMDs are 