#!/usr/bin/env python3
"""Enforce the native, dependency-free Android architecture."""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ANDROID = ROOT / "apps" / "mobile" / "android"
REQUIRED = (
    "settings.gradle",
    "build.gradle",
    "app/build.gradle",
    "app/proguard-rules.pro",
    "app/src/main/AndroidManifest.xml",
    "app/src/main/java/com/parrotcare/mobile/MainActivity.java",
    "app/src/main/java/com/parrotcare/mobile/audio/AudioRecorder.java",
    "app/src/main/java/com/parrotcare/mobile/data/LocalStore.java",
    "app/src/main/res/layout/activity_main.xml",
    "app/src/main/res/values/strings.xml",
    "scripts/build-release.sh",
)
FORBIDDEN = {
    r"\bandroidx\.": "AndroidX",
    r"\bkotlin\b": "Kotlin",
    r"\bcompose\b": "Compose",
    r"\bWebView\b": "WebView shell",
    r"\bflutter\b": "Flutter",
    r"\bcapacitor\b": "Capacitor",
    r"\breact[ -]?native\b": "React Native",
}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


for relative in REQUIRED:
    if not (ANDROID / relative).is_file():
        fail(f"Missing Android source: apps/mobile/android/{relative}")

java_sources = list((ANDROID / "app" / "src" / "main" / "java").rglob("*.java"))
xml_sources = list((ANDROID / "app" / "src" / "main").rglob("*.xml"))
source_files = [
    *java_sources,
    *xml_sources,
    *ANDROID.glob("*.gradle"),
    ANDROID / "app" / "build.gradle",
    ANDROID / "gradle.properties",
]
combined = "\n".join(path.read_text(encoding="utf-8") for path in source_files)
for pattern, name in FORBIDDEN.items():
    if re.search(pattern, combined, flags=re.IGNORECASE):
        fail(f"Forbidden Android runtime/framework detected: {name}")

app_gradle = (ANDROID / "app" / "build.gradle").read_text(encoding="utf-8")
dependencies = re.search(r"dependencies\s*\{(?P<body>.*?)\}", app_gradle, flags=re.DOTALL)
if dependencies is None:
    fail("Android dependencies block is missing")
dependency_lines = [
    line.strip()
    for line in dependencies.group("body").splitlines()
    if line.strip() and not line.strip().startswith("//")
]
if dependency_lines:
    fail(f"Android dependencies must stay empty: {dependency_lines}")
if "minifyEnabled true" not in app_gradle or "shrinkResources true" not in app_gradle:
    fail("Android release must enable R8 minification and resource shrinking")

manifest = (ANDROID / "app" / "src" / "main" / "AndroidManifest.xml").read_text(encoding="utf-8")
for metadata in ('package="com.parrotcare.mobile"', 'android:versionCode=', 'android:versionName='):
    if metadata not in manifest:
        fail(f"Android manifest is missing manual-build metadata: {metadata}")

manual_build = (ANDROID / "scripts" / "build-release.sh").read_text(encoding="utf-8")
for tool in ("aapt2", "javac", "d8", "zipalign", "apksigner"):
    if tool not in manual_build:
        fail(f"Android manual build is missing tool: {tool}")

for xml_path in xml_sources:
    ET.parse(xml_path)

java_bytes = sum(path.stat().st_size for path in java_sources)
print(f"Android architecture check passed: platform-only Java, {java_bytes} source bytes.")
