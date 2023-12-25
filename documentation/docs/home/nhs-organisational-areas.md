---
title: NHS Organisational Areas and Index of Multiple Deprivation
author: Dr Simon Chapman
---

# UK Areas

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

Within healthcare, there are several other important organisational boundaries.

Integrated Care Boards were introduced on 1st July 2022, taking over from Sustainability and Transformation Partnerships (STPs) and 106 Clinical Commissioning Groups (CCGs) as the top-level organisational units for planning and commissioning health and social care. Commissioning now is controlled by the 42 ICBs (and ICPs or integrated care partnerships). Other hierarchies include providers (such as NHS Trusts, Mental Health Trusts, GP surgeries, pharmacies, ambulance services etc) and Primary Care Networks (PCNs).

## Indices of Multiple Deprivation (IMD)

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
| *32844 LSOAs*                    | *1909 LSOAs*          | *6976 Data Zones* | *890 SOAs*                        |
| *2019 data*                      | *2019 data*           | *2020 data*       | *2017 data*                       |

In England, there are also subdomains for education (children and young people and adult skills), barriers to housing and services (geographical barriers and wider barriers) and living environment (indoors and outdoors).

These domains are then weighted and contribute to the final index of multiple deprivation score. Based on the score in each LSOA, LSOAs are then ranked by deprivation score, and then split into quantiles (with the lower quantiles the most deprived). It is important to say that the rankings do not compare between countries - that is a given decile in one country is not the same as the same decile in another, and this is because the scores are not standardised across the UK, only across each nation. An attempt to do this has been made by [MySociety](https://github.com/mysociety/composite_uk_imd) who have published a Composite UK IMD which brings together all the datasets across the devolved nations. In the process, however, a lot of the detail is lost so whilst this allows the user to compare deprivation scores across countries, [it is not possible to compare the subdomains](https://github.com/mysociety/composite_uk_imd/issues/2). For our purposes, therefore, we will use the individual countries scores, but report these with an appropriate warning.