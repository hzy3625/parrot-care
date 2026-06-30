#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SDK_DIR="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
BUILD_TOOLS_VERSION="${ANDROID_BUILD_TOOLS_VERSION:-35.0.0}"
BUILD_TOOLS="$SDK_DIR/build-tools/$BUILD_TOOLS_VERSION"
PLATFORM_JAR="$SDK_DIR/platforms/android-35/android.jar"
APP_DIR="$ROOT_DIR/app/src/main"
OUT_DIR="$ROOT_DIR/build/manual"
RELEASE_DIR="$ROOT_DIR/../release/android"
MANIFEST="$APP_DIR/AndroidManifest.xml"
VERSION_NAME="$(sed -n 's/.*android:versionName="\([^"]*\)".*/\1/p' "$MANIFEST" | head -1)"
OUTPUT_APK="$RELEASE_DIR/parrot-care-v${VERSION_NAME}.apk"

if [[ -z "$SDK_DIR" || ! -f "$PLATFORM_JAR" ]]; then
  echo "Android SDK 35 not found. Set ANDROID_HOME or ANDROID_SDK_ROOT." >&2
  exit 2
fi

for tool in aapt2 d8 zipalign apksigner; do
  if [[ ! -x "$BUILD_TOOLS/$tool" ]]; then
    echo "Missing Android build tool: $BUILD_TOOLS/$tool" >&2
    exit 2
  fi
done

rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR/classes" "$OUT_DIR/dex" "$OUT_DIR/compiled" "$RELEASE_DIR"

"$BUILD_TOOLS/aapt2" compile --dir "$APP_DIR/res" -o "$OUT_DIR/compiled/resources.zip"
"$BUILD_TOOLS/aapt2" link \
  -I "$PLATFORM_JAR" \
  --manifest "$MANIFEST" \
  --java "$OUT_DIR/generated" \
  -o "$OUT_DIR/unsigned.apk" \
  "$OUT_DIR/compiled/resources.zip"

find "$APP_DIR/java" "$OUT_DIR/generated" -name '*.java' > "$OUT_DIR/sources.txt"
javac -source 17 -target 17 \
  -classpath "$PLATFORM_JAR" \
  -d "$OUT_DIR/classes" \
  @"$OUT_DIR/sources.txt"

find "$OUT_DIR/classes" -name '*.class' > "$OUT_DIR/classes.txt"
"$BUILD_TOOLS/d8" \
  --lib "$PLATFORM_JAR" \
  --min-api 26 \
  --output "$OUT_DIR/dex" \
  @"$OUT_DIR/classes.txt"

(cd "$OUT_DIR/dex" && zip -q "$OUT_DIR/unsigned.apk" classes.dex)

SIGNING_DIR="$ROOT_DIR/build/signing"
KEYSTORE="$SIGNING_DIR/local-release.keystore"
mkdir -p "$SIGNING_DIR"
if [[ ! -f "$KEYSTORE" ]]; then
  keytool -genkeypair \
    -keystore "$KEYSTORE" \
    -storepass android \
    -keypass android \
    -alias parrot-care \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -dname "CN=ParrotCare Local Build,O=Local,C=CN"
fi

"$BUILD_TOOLS/zipalign" -f 4 "$OUT_DIR/unsigned.apk" "$OUT_DIR/aligned.apk"
"$BUILD_TOOLS/apksigner" sign \
  --ks "$KEYSTORE" \
  --ks-key-alias parrot-care \
  --ks-pass pass:android \
  --key-pass pass:android \
  --v4-signing-enabled false \
  --out "$OUTPUT_APK" \
  "$OUT_DIR/aligned.apk"

"$BUILD_TOOLS/apksigner" verify --verbose "$OUTPUT_APK"
echo "APK created: $OUTPUT_APK"
