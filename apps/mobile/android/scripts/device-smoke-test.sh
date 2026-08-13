#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
RELEASE_DIR="$ROOT_DIR/../release/android"
PACKAGE_NAME="com.parrotcare.mobile"

if [[ -z "$SDK_DIR" || ! -x "$SDK_DIR/platform-tools/adb" ]]; then
  echo "Android platform-tools not found. Set ANDROID_HOME or ANDROID_SDK_ROOT." >&2
  exit 2
fi

APK="$(find "$RELEASE_DIR" -maxdepth 1 -name 'parrot-care-v*.apk' -print | sort | tail -1)"
if [[ -z "$APK" ]]; then
  echo "No release APK found under $RELEASE_DIR. Run make android-release first." >&2
  exit 2
fi

ADB="$SDK_DIR/platform-tools/adb"
DEVICE_COUNT="$("$ADB" devices | awk 'NR > 1 && $2 == "device" { count++ } END { print count + 0 }')"
if [[ "$DEVICE_COUNT" -lt 1 ]]; then
  echo "No authorized Android device found. Enable USB debugging and authorize this computer." >&2
  "$ADB" devices
  exit 2
fi

echo "Installing $APK"
"$ADB" install -r "$APK"

echo "Launching $PACKAGE_NAME"
"$ADB" shell monkey -p "$PACKAGE_NAME" -c android.intent.category.LAUNCHER 1 >/dev/null

echo "Recent app logs:"
"$ADB" logcat -d -t 200 | grep "$PACKAGE_NAME" || true

echo "Smoke test setup complete. Manually verify: record, import, create observation, edit detail, export/import backup."
