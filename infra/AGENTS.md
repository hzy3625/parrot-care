# Infrastructure Instructions

## Scope

This directory owns Docker Compose, Dockerfiles, the API entrypoint, and Nginx. Build contexts are the repository root so images can consume files from `apps` and `ml` without duplicating them.

## Commands

```bash
docker compose -f infra/docker-compose.yml config
make docker-up
make verify-docker
make docker-down
```

## Rules

- Keep service names `web`, `api`, `db`, and `minio` stable because proxy and dependency configuration use them.
- Web image copies only `apps/web`; API image copies `apps/api` plus `ml/models/audio_classifier.pt`.
- Secrets come from environment variables or an untracked `.env`, never from committed Compose values.
- Health checks must exercise the service from inside its container.
- Pin major runtime versions and avoid mutable application data inside image layers.
