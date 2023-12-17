---
title: Getting started
author: Dr Simon Chapman
---

## Getting Started

Written in python 3.11 and django-rest-framework. We recommend using `pyenv` or similar python version manager and virtual environment manager.

### Option One

1. clone the repo
2. ```cd rcpch_census_platform```
3. ```pip install -r requirements/common-requirements.txt```
4. ```python manage.py createsuperuser --username username --email username@email.com```
5. ```python manage.py makemigrations```
6. ```python manage.py migrate```
7. ```python manage.py seed --mode='add_organisational_areas'```
8. ```python manage.py seed --mode='add_english_imds'```
9. ```python manage.py seed --mode='add_welsh_imds'```
10. ```python manage.py seed --mode='add_scottish_imds'```
11. ```python manage.py seed --mode='add_northern_ireland_imds'```

This latter step will take several minutes as it populates the database with all the census and deprivation data. If successful, it should yield the following message:
> ![alt rcpch-census-db](static/images/census_db_screenshot.png?raw=true)

The final step is to run the server:
```python manage.py runserver```

### Docker Compose development install

<!-- the below needs a rewrite to include 'docker compose exec web' in front of all the commands -->
1. clone the repo
2. ```cd rcpch_census_platform```
3. ```s/docker-init```

If you navigate to the base url ```http://rcpch-census-platform.localhost/v1/``` and login, it should be possible then to view the data. Alternatively, add the token to Postman.

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
