#!/usr/bin/env python3
"""Verify that the API imports, exposes its contract, and answers health checks."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from httpx import ASGITransport, AsyncClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "apps" / "api"))

from main import app  # noqa: E402


def print_contract() -> None:
    paths = app.openapi()["paths"]
    operation_count = sum(len(operations) for operations in paths.values())
    print(f"API contract: {len(paths)} paths, {operation_count} operations")
    for path, operations in sorted(paths.items()):
        methods = ",".join(method.upper() for method in operations)
        print(f"  [{methods}] {path}")


async def verify_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "ok":
        raise RuntimeError(f"Unexpected health response: {payload}")
    print(f"Health check: {response.status_code} {payload['status']}")


if __name__ == "__main__":
    print_contract()
    asyncio.run(verify_health())
