# Native Android Instructions

## Scope

Android is the only supported mobile platform. It is a native Java/XML application, not a WebView wrapper. Core recording and local records must work without the API.

## Architecture

```text
android/app/src/main/java/com/parrotcare/mobile/
  MainActivity.java  Platform Activity and permission flow
  audio/             Platform audio recording and playback
  data/              SQLiteOpenHelper and file persistence
android/app/src/main/res/  XML layouts and strings
release/android/           Final APK/AAB delivery location
```

## Hard rules

- Use Java and Android platform APIs. Do not add Kotlin, Compose, AndroidX, Flutter, React Native, Capacitor, Cordova, or a WebView application shell.
- Keep `dependencies {}` empty unless a capability is impossible with the Android SDK and the size impact is documented first.
- Use `SQLiteOpenHelper` and app-private files; do not add Room or another database runtime.
- Use platform `MediaRecorder`; add `MediaPlayer` only when playback is implemented, and do not bundle an audio framework.
- Request microphone permission only when recording starts.
- Core flows never require `apps/api`; optional synchronization must fail without losing local data.
- Prefer the direct Android SDK build in `android/scripts/build-release.sh`; do not add build-time package downloads for routine releases.
- Gradle metadata is retained only for IDE compatibility and must keep `dependencies {}` empty.
- Never commit APK/AAB files, Gradle caches, signing keys, keystores, or passwords.

## Verification

Run `make check-android`. On a configured Android SDK machine, run `make android-release` and verify permission denial/retry, recording, process restart, offline launch, rotation, back navigation, and upgrade data retention.

Architecture detail: `../../docs/architecture/native-android.md`.
