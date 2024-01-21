---
title: Getting started
author: Dr Simon Chapman
---

## Getting Started

Written in python 3.11 and django-rest-framework, with a sqlite3 backend, this is a lightweight containerized application - with 2 containers: one with django rest framework and a database, the other with documentation in mkdocs.

The easiest way to get started is using docker. This is how it is used in production.

The start scripts are all in the `s` folder. It may be necessary to change permissions to this folder first, from within the project root by:
`chmod+x ~/s`

**Note that nothing will work without a `.envs/.env` file with environment variables. An example file is provided.

The start script creates 3 linked docker containers under the umbrella name `rcpch-census-platform`:

1. **django-1** The API and Sqlite3 database
2. **mkdocs-1** All documentation
3. **caddy-1** web server

Once all docker containers have been instantiated, django runs through the migrations which create the tables in the database and seed them with data. None of this data is proprietary and is openly available on the public internet. As the database is seeded, progress is logged to the console within the django container. The database is committed to the repo, so this escapes the need to seed the database each time.

### Steps

1. clone the repo
2. ```s/up```

If you navigate to [https://rcpch-census-platform.localhost/rcpch-census-platform/api/v1/swagger-ui/#/](https://rcpch-census-platform.localhost/rcpch-census-platform/api/v1/swagger-ui/#/) the Open API Specification and schemas are visible. If only the base url [https://rcpch-census-platform.localhost/rcpch-census-platform/api/v1/](https://rcpch-census-platform.localhost/rcpch-census-platform/api/v1/) is used, the django browsable API can be found.
