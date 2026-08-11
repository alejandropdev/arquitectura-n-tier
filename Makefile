SHELL := /bin/bash
COMPOSE := docker compose

.DEFAULT_GOAL := help

help:            ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

env:             ## Crea .env a partir de .env.example si no existe
	@test -f .env || cp .env.example .env

build: env       ## Construye las imágenes
	$(COMPOSE) build

up: env          ## Levanta todo el despliegue
	$(COMPOSE) up -d --build
	@echo "Web:      http://localhost:8080"
	@echo "API auth: http://localhost:8081/health"

down:            ## Detiene los contenedores (conserva los datos)
	$(COMPOSE) down

clean:           ## Detiene y borra volúmenes (reinicia la base de datos)
	$(COMPOSE) down -v

ps:              ## Estado de los contenedores
	$(COMPOSE) ps

logs:            ## Logs estructurados de todos los servicios
	$(COMPOSE) logs -f

logs-auth:       ## Logs del Tier 2
	$(COMPOSE) logs -f auth-service-1 auth-service-2

venv:            ## Entorno virtual local para las pruebas
	python3 -m venv .venv
	./.venv/bin/pip install -q -r auth-service/requirements-dev.txt -r web/requirements-dev.txt

test: venv       ## Ejecuta todas las pruebas (Tier 1 + Tier 2 + Tier 3)
	cd auth-service && ../.venv/bin/python -m pytest
	cd web && ../.venv/bin/python -m pytest

coverage: venv   ## Pruebas con reporte de cobertura
	cd auth-service && ../.venv/bin/python -m pytest --cov=app --cov-report=term-missing
	cd web && ../.venv/bin/python -m pytest --cov=app --cov-report=term-missing

smoke:           ## Prueba end-to-end contra el despliegue en Docker
	bash scripts/smoke.sh

chaos:           ## Demuestra la tolerancia a fallas (apaga una instancia del Tier 2)
	bash scripts/chaos.sh

.PHONY: help env build up down clean ps logs logs-auth venv test coverage smoke chaos
