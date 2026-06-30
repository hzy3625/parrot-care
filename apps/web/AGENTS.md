# Web PWA Instructions

## Scope

This directory contains the only active frontend. One responsive React + TypeScript PWA supports desktop and mobile. Mobile core behavior is local-first and must not require the API.

## Commands

Run from the repository root:

```bash
npm --prefix apps/web ci
npm --prefix apps/web run dev
npm --prefix apps/web run check
```

## Map

```text
src/data/    IndexedDB repository and future optional sync adapters
src/domain/  Categories, labels, and pure domain formatting
src/pages/   Route-level UI; no direct network access
src/types/   Shared frontend contracts
public/      PWA icons and static assets
```

## Rules

- Keep one responsive implementation; do not add a separate mobile app for the same workflow.
- Page components call repository functions, never `fetch`, Axios, or hard-coded service URLs.
- Commit a local IndexedDB transaction before showing success. Remote sync, when added, happens afterward.
- Use HashRouter so installed and static-hosted builds can restore routes offline.
- Keep touch targets at least 44px and preserve labels, keyboard focus, and reduced-motion behavior.
- Revoke temporary object URLs and stop MediaStream tracks during cleanup.
- Do not store audio blobs or large payloads in `localStorage`.

## Verification

Run `npm --prefix apps/web run check`, then exercise the changed flow at 360px and at >=1024px. For persistence changes, reload and confirm IndexedDB data survives. PWA and microphone behavior require HTTPS outside localhost.

Architecture details: `../../docs/architecture/local-first.md`.
