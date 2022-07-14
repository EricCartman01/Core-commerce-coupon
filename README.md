[![Quality Gate Status](https://sonar.faci.ly/api/project_badges/measure?project=84ad7b7d-4907-49af-a52b-c305d22c2efd&metric=alert_status&token=cd07b25611c7e507c820427568e5adb623ac5559)](https://sonar.faci.ly/dashboard?id=84ad7b7d-4907-49af-a52b-c305d22c2efd)

# Coupon

Python FastAPI and SQLalchemy ORM over Postgres database

## Technologies
- Python 3.9
- FastApi - Framework
- SQLalchemy - ORM
- Docker - Project Structure
- Docker-compose - Development Environment
- Postgresql - Development Database
- Alembic - Database migration tool
- Poetry - Libraries management tool for Python.

## Enviroments

### Development

Healthcheck: https://core-commerce-coupon.staging.faci.ly/health

Swagger: https://core-commerce-coupon.development.faci.ly/docs

Newrelic:

### Homolog

Healthcheck: https://core-commerce-coupon.staging.faci.ly/health

Swagger: https://core-commerce-coupon.staging.faci.ly/docs

Newrelic:

## How to use?

### Docker

1. Clone this repository

2. To copy `.env.example` to `.env`, run: `make copy-envs`

3. Build docker image and run migrates: `make build`

4. Run api: `make run`

5. In your browser call: [Swagger Localhost](http://localhost:8000/api/docs)

#### Comands

Executing commands inside the container:

``` bash
make run-bash
```

Generate migration: *

``` bash
make run-migrations name=<MODULE NAME>
```

Additional dependencies: *

``` bash
make run-poetry-add name=<LIB NAME>
```

* Must be inside the container

### Locally

1. Clone this repository.
2. To initialize and install dependencies, run: `make init`
3. To apply the migrations, run: `make migrate`
4. Run: `make run-local`
5. In your browser call: [Swagger Localhost](http://localhost:8000/docs)

Note: To run locally, you must have a database service configured. Docker can be used to
quickly start this service.

Docker command example:
``` bash
docker run --name core-commerce-postgres -e POSTGRES_PASSWORD=core_commerce -e POSTGRES_USER=core_commerce -e POSTGRES_DB=core_commerce -p 5432:5432 -d postgres
```

#### Testing

To test, just run `make test`.
# Core-commerce-coupon
