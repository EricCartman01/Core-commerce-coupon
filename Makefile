export PYTHONDONTWRITEBYTECODE=1

.PHONY=help

help:  ## This help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

clean:  ## Remove cache files
	@find . -name "*.pyc" | xargs rm -rf
	@find . -name "*.pyo" | xargs rm -rf
	@find . -name "__pycache__" -type d | xargs rm -rf


###
# Dependencies section
###
_base-pip:
	@pip install -U pip poetry wheel

system-dependencies:
	@sudo apt-get update -y && sudo apt-get install -y libpq-dev

dev-dependencies: _base-pip  ## Install development dependencies
	@poetry install

export-requirements: _base-pip
	@poetry export --without-hashes --dev -f requirements.txt > requirements.txt

ci-dependencies:
	@pip install -r requirements.txt

dependencies: _base-pip  ## Install dependencies
	@poetry install --no-dev

outdated:  ## Show outdated packages
	@poetry show --outdated


###
# Lint section
###
_flake8:
	@flake8 --show-source app/

_isort:
	@isort --check-only app/

_black:
	@black --diff --check app/

_isort-fix:
	@isort app/ tests/

_black-fix:
	@black app/ tests/

_dead-fixtures:
	@pytest app/ --dead-fixtures

_mypy:
	@mypy app/

lint: _flake8 _isort _black _dead-fixtures  ## Check code lint
format-code: _isort-fix _black-fix  ## Format code


###
# Tests section
###
test: clean  ## Run tests
	@pytest tests/

test-coverage: clean  ## Run tests with coverage output
	@pytest tests/ --cov app/ --cov-report term-missing --cov-report xml

test-matching: clean  ## Run tests by match ex: make test-matching k=name_of_test
	@pytest -k $(k) tests/

test-security: clean  ## Run security tests with bandit and safety
	@python -m bandit -r app -x "test"
	@python -m safety check


###
# Migrations DB section
###
migrations:  ## Create named migrations file. Ex: make migrations name=<migration_name>
	@alembic revision --autogenerate --message $(name)

migrate:  ## Apply local migrations
	@alembic upgrade head

history:  ## migrations history
	@alembic history

branches: ## migrations branch point
	@alembic branches --verbose

merge: ## Create named migrations file from multiplous heads. Ex: make merge m=<migration_name>
	@alembic merge heads -m ${m}

pre-commit-install:  ## Install pre-commit hooks
	@pre-commit install

pre-commit-uninstall:  ## Uninstall pre-commit hooks
	@pre-commit uninstall


###
# Run local section
###
copy-envs:  ## Copy `.env.example` to `.env`
	@cp -n .env.example .env

init: dev-dependencies pre-commit-install copy-envs ## Initialize project

run-local:  ## Run server
	@python -m app


###
# Docker section
###
build:  ## Docker: Initialize project
	docker-compose build
	make run-migrate

run-docker:  ## Docker: Run server
	docker-compose run --service-ports --rm api bash -c "make run-local"

run-bash:  ## Docker: Get bash from container
	docker-compose run --service-ports --rm api bash

run-pytest:  ## Docker: Run tests
	docker-compose run --service-ports --no-deps --rm api bash -c "make test"

run-coverage:  ## Docker: Run tests with coverage output
	docker-compose run --service-ports --rm api bash -c "make test-coverage"

run-format-code:  ## Docker: Format code
	docker-compose run --service-ports --no-deps --rm api bash -c "make format-code"

run-code-convention:  ## Docker: Check code lint
	docker-compose run --service-ports --no-deps --rm api bash -c "make lint"

run-poetry-add:  ## Docker: Add dependency with poetry. Ex: make run-poetry-add name=<migration_name>
	docker-compose run --service-ports --no-deps --rm api bash -c "poetry add $(name)"

run-migrations:  ## Docker: Create named migrations file. Ex: make run-migrations name=<migration_name>
	docker-compose run --service-ports --rm api bash -c "make migrations name=$(name)"

run-migrate:  ## Docker: Apply migrations
	docker-compose run --service-ports --rm api bash -c "make migrate"


###
# Default run
###
run: run-docker  ## Default execution is by docker


###
# Stuff section
###
bump:
	@cz bump --check-consistency
