# ParrotCare Agent Map

## Project model

ParrotCare is a full-stack monorepo for parrot audio and health records. `apps/web` is a local-first React PWA that must complete its core workflow without a server. `apps/api` is an optional FastAPI service for accounts, analysis, sync, and notifications. `ml` owns datasets, training tools, and the canonical model artifact.

This file is a map. Follow the nearest nested `AGENTS.md` for module-specific rules and use linked documents for details.

## Fast commands

| Goal | Command |
| --- | --- |
| Show commands | `make help` |
| Install dependencies | `make install` |
| Start web | `make dev-web` |
| Start API | `make dev-api` |
| Check repository | `make check` |
| Build PWA | `make build` |
| Start full stack | `make docker-up` |
| Stop full stack | `make docker-down` |

If only web code changed, run `make check-structure check-web`. If API, shared audio services, models, or migrations changed, also run `make test-api`.

## Repository map

```text
apps/
  web/       React + TypeScript PWA; local-first core product
  api/       FastAPI service; optional enhancement for the PWA
  mobile/    Android wrapper and local release layout
ml/
  datasets/  Dataset tools and local data guidance
  training/  Feature extraction and model training commands
  models/    Canonical runtime model artifact
infra/
  docker/    Dockerfiles, entrypoint, and Nginx configuration
  docker-compose.yml
scripts/
  migration/     Data migration commands
  verification/  Automated repository and deployment checks
docs/
  architecture/  Current system boundaries and decisions
  requirements/  Active domain and data requirements
  testing/       Verification guidance
```

## Hard rules

1. Mobile core flows must work without `apps/api`, PostgreSQL, or MinIO.
2. Pages in `apps/web/src/pages` never call HTTP directly. Use `src/data` or an optional sync adapter.
3. Audio blobs belong in IndexedDB, not `localStorage`.
4. API routes validate and translate protocol data; business logic belongs in `apps/api/app/services`.
5. The canonical model is `ml/models/audio_classifier.pt`. Do not add model copies under apps.
6. Android is native Java/XML with platform storage and audio APIs. Do not introduce a WebView shell or cross-platform runtime.
7. Never commit `node_modules`, `dist`, `.env`, databases, user audio, credentials, mobile signing keys, APK/AAB files, or `.DS_Store`.
8. File and import casing must match exactly for Linux container builds.
9. A change is incomplete until its relevant build, tests, and user flow have been verified.

`make check-structure` enforces the most important repository and web data-boundary rules.

## Module instructions

| Scope | Instructions |
| --- | --- |
| Web PWA | `apps/web/AGENTS.md` |
| FastAPI | `apps/api/AGENTS.md` |
| Android packaging | `apps/mobile/AGENTS.md` |
| ML and datasets | `ml/AGENTS.md` |
| Containers and deployment | `infra/AGENTS.md` |

## Documentation

Start at `docs/README.md`. Current architecture is in `docs/architecture/`; local setup and the verification matrix are in `docs/development.md` and `docs/testing/verification.md`.

Update this map only for repository-wide commands, boundaries, and hard rules. Put implementation detail in the nearest module instructions or a focused document.
