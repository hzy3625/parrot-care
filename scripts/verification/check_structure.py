#!/usr/bin/env python3
"""Validate repository boundaries that commonly confuse people and coding agents."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_PATHS = (
    "AGENTS.md",
    "apps/web/AGENTS.md",
    "apps/api/AGENTS.md",
    "apps/mobile/AGENTS.md",
    "apps/mobile/android/README.md",
    "apps/mobile/android/app/build.gradle",
    "apps/mobile/android/scripts/build-release.sh",
    "apps/mobile/release/android/README.md",
    "ml/AGENTS.md",
    "infra/AGENTS.md",
    "docs/README.md",
)
FORBIDDEN_TRACKED_PARTS = ("node_modules/", "dist/", ".DS_Store", ".apk", ".aab", ".keystore")
FORBIDDEN_WEB_PATTERNS = {
    r"https?://(?:localhost|127\.0\.0\.1)": "页面不得硬编码本机后端地址",
    r"\bfetch\s*\(": "页面应通过 repository 或 adapter 访问数据",
    r"\baxios\b": "页面应通过 repository 或 adapter 访问数据",
}


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return result.stdout.splitlines()


def main() -> int:
    errors: list[str] = []

    for relative_path in REQUIRED_PATHS:
        if not (ROOT / relative_path).exists():
            errors.append(
                f"WHAT: 缺少 {relative_path}\n"
                "WHY: AI Agent 无法找到对应模块的入口规则\n"
                "HOW: 恢复该文件并保持文档导航有效"
            )

    for path in ROOT.rglob(".DS_Store"):
        if ".git" in path.relative_to(ROOT).parts:
            continue
        errors.append(
            f"WHAT: 存在临时文件 {path.relative_to(ROOT)}\n"
            "WHY: 操作系统产物会污染仓库差异\n"
            "HOW: 删除该文件并保留 .gitignore 规则"
        )

    for relative_path in tracked_files():
        if any(part in relative_path for part in FORBIDDEN_TRACKED_PARTS):
            errors.append(
                f"WHAT: Git 跟踪了生成文件 {relative_path}\n"
                "WHY: 依赖或构建产物会制造巨大差异且不可移植\n"
                "HOW: 从 Git 索引移除，并通过 lockfile 重新生成"
            )
            if len(errors) >= 20:
                break

    pages_dir = ROOT / "apps" / "web" / "src" / "pages"
    for source_path in pages_dir.glob("*.tsx"):
        content = source_path.read_text(encoding="utf-8")
        for pattern, reason in FORBIDDEN_WEB_PATTERNS.items():
            if re.search(pattern, content):
                errors.append(
                    f"WHAT: {source_path.relative_to(ROOT)} 违反数据边界\n"
                    f"WHY: {reason}\n"
                    "HOW: 将访问逻辑迁入 src/data 或独立同步 adapter"
                )

    if errors:
        print("\n\n".join(errors), file=sys.stderr)
        print(f"\nStructure check failed with {len(errors)} issue(s).", file=sys.stderr)
        return 1

    print("Structure check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
