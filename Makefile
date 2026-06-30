.DEFAULT_GOAL := help

.PHONY: help install install-ml dev dev-web dev-api check check-structure check-web check-android test test-api build android-release docker-up docker-down verify-docker

help:
	@echo "ParrotCare development commands"
	@echo "  make install          Install web and API dependencies"
	@echo "  make install-ml       Install optional ML dependencies"
	@echo "  make dev-web          Start the responsive PWA"
	@echo "  make dev-api          Start the optional FastAPI service"
	@echo "  make check            Run structure, web, and API checks"
	@echo "  make check-android    Enforce the platform-only Android architecture"
	@echo "  make android-release  Build an installable native APK with Android SDK tools"
	@echo "  make build            Build the production PWA"
	@echo "  make docker-up        Start the complete stack"

install:
	npm --prefix apps/web ci
	python3 -m venv .venv
	.venv/bin/python -m pip install -r apps/api/requirements-dev.txt

install-ml:
	.venv/bin/python -m pip install -r ml/requirements.txt

dev: dev-web

dev-web:
	npm --prefix apps/web run dev

dev-api:
	cd apps/api && ../../.venv/bin/python start.py

check: check-structure check-web check-android test-api

check-structure:
	python3 scripts/verification/check_structure.py

check-web:
	npm --prefix apps/web run check

check-android:
	python3 scripts/verification/check_android.py

test: check

test-api:
	cd apps/api && ../../.venv/bin/python -m pytest tests -q

build:
	npm --prefix apps/web run build

android-release:
	apps/mobile/android/scripts/build-release.sh

docker-up:
	docker compose -f infra/docker-compose.yml up -d

docker-down:
	docker compose -f infra/docker-compose.yml down

verify-docker:
	python3 scripts/verification/verify_docker.py
