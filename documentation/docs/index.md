---
title: Introduction
author: Dr Simon Chapman
---
!!! info "Guidance for Researchers"
    Go to the [Researchers' Guide](./researchers/api.md) for guidance on retrieving census data.

## RCPCH Census Platform

This project is a python 3.11 / Django Rest Framework project providing UK census and organisational data as a service.

In particular it serves the following:

1. **Index of multiple deprivation against a postcode anywhere in the UK**
2. **List of all secondary care organisations in the UK where children are cared for.**
This latter service in particular is important as such a list does not exist elsewhere - it pulls together acute and community hospitals across the UK, as well the NHS organisational boundaries within which they fall (Trust/Local Health Board, Integrated Care Board, NHS Region). It also references which Paediatric Diabetes Unit they form part of, or which OPEN UK children's epilepsy group they fall into.

These 2 services support all RCPCH applications, in particular the Epilepsy12 and National Paediatric Diabetes Audits.

They are though open to anyone and do not require authentication.

The project is dockerised, and has containers for [Postgresql](https://www.postgresql.org/), [redis](https://redis.com/), [celery](https://docs.celeryq.dev/en/stable/django/first-steps-with-django.html) and [celery-beat](https://docs.celeryq.dev/en/stable/reference/celery.beat.html) for async and scheduled tasks. This documentation is also in a separate container and built with [MkDocs](https://www.mkdocs.org/)

### Other services

There are also endpoints that list health organisational areas across the NHS, including items such as access to green space. RCPCH is open to storing data of any kind in this resource to support research and audit into children's health and environment. For users with datasets they would like RCPCH to host, or suggestions of datasets they would like to incorporate, please post as issues to the [repository](https://github.com/rcpch/rcpch-census-platform/issues).

<p align="center">
    <p align="center">
    <img src='../docs/_assets/_images/rcpch-logo-mobile.4d5b446caf9a.svg' alt='RCPCH Logo'>
    </p>
</p>

## Why is it needed?

The [Office of National Statistics](https://www.ons.gov.uk) publishes all the Census data exhaustively - this project is not intended to replace it. There is a need though for RCPCH to be able to describe the lived environment and experience of children and young people in a meaningful way, to inform research, audit and clinical practice. The project will curate social and environmental data where they have impact on children's health or on paediatrics, available to clinicians and researchers. It is a work in progress.
