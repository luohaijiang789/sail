.PHONY: install dev test lint format typecheck migrate migrate-new run-worker docker-up docker-down

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	ruff check app/ workers/ extractors/ scanners/ ai/ tests/

format:
	ruff format app/ workers/ extractors/ scanners/ ai/ tests/

typecheck:
	mypy app/ workers/ extractors/ scanners/ ai/

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(MSG)"

run-api:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

run-worker-fetch:
	celery -A workers.celery_app worker -Q source_fetch -c 4 -n fetch@%h --loglevel=info

run-worker-build:
	celery -A workers.celery_app worker -Q java_build_jdk17 -c 2 -n build@%h --loglevel=info

run-worker-codeql:
	celery -A workers.celery_app worker -Q codeql_query -c 2 -n codeql@%h --loglevel=info

run-worker-ai:
	celery -A workers.celery_app worker -Q ai_analysis -c 4 -n ai@%h --loglevel=info

run-worker-post:
	celery -A workers.celery_app worker -Q result_process,source_extract -c 4 -n post@%h --loglevel=info

docker-up:
	cd docker && docker-compose up -d

docker-down:
	cd docker && docker-compose down

docker-logs:
	cd docker && docker-compose logs -f

docker-build:
	cd docker && docker-compose build

docker-build-base:
	docker build -f docker/Dockerfile.base -t sail-base:latest .

docker-build-build:
	docker build -f docker/Dockerfile.build -t sail-build:latest --build-arg CODEQL_VERSION=2.22.4 .

docker-build-codeql:
	docker build -f docker/Dockerfile.codeql -t sail-codeql:latest --build-arg CODEQL_VERSION=2.22.4 .

docker-ps:
	cd docker && docker-compose ps
