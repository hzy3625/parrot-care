# FastAPI Instructions

## Scope

This service provides optional accounts, model-backed analysis, synchronization, notifications, and administration. The PWA must remain usable when this service is unavailable.

## Commands

```bash
cd apps/api
../../.venv/bin/python start.py
../../.venv/bin/python -m pytest tests -q
```

## Map

```text
app/api/       HTTP and WebSocket protocol layer
app/models/    SQLAlchemy models and Pydantic schemas
app/services/  Business logic, notifications, and audio analysis
alembic/       Database migrations
tests/         API and service tests
```

## Rules

- Routes validate input, resolve authentication, and call services; do not embed reusable business logic in routes.
- Use `app/db.py` for database lifecycle and sessions.
- Configuration priority is environment > `apps/api/.env` > safe development defaults.
- Read the model path from `settings.AUDIO_MODEL_PATH`; the canonical artifact lives in `ml/models`.
- Preserve Mock/fallback behavior when optional ML dependencies or model artifacts are unavailable.
- Never make an API write a prerequisite for the web app's local save.
- Add or update focused tests for every contract or service behavior change.

## Verification

Run targeted tests while developing and `make test-api` before handoff. For schema or migration changes, test both SQLite development startup and the PostgreSQL container path.

Root `make install` installs API and test dependencies. Run `make install-ml` only for audio feature, training, or real model inference work.
