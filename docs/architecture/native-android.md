# Native Android Architecture

## Decision

The Android app uses only Android platform APIs and Java. It does not embed the Web PWA and does not use Kotlin, Compose, AndroidX, Room, Flutter, React Native, Capacitor, Cordova, or third-party UI/audio/database libraries.

This keeps the application DEX, resources, startup path, and dependency surface small. Releases use Android SDK command-line tools directly, following the proven `mistake-notebook` approach; Gradle files remain only for IDE compatibility.

## Layers

```text
Activity + XML Views
       ↓
small Java use-case classes
       ↓
SQLiteOpenHelper + app-private files + MediaRecorder
       ↓
optional HttpURLConnection sync adapter (future)
```

- UI: platform `Activity`, `Fragment` only when navigation requires it, XML resources.
- Domain: plain Java value objects and use-case classes without Android dependencies where practical.
- Storage: event metadata in SQLite; audio in `Context.getFilesDir()` with paths stored in SQLite.
- Audio: AAC in an MPEG-4 container using a low bitrate suitable for voice-like parrot recordings.
- Network: absent from core flows. A future adapter may use `HttpURLConnection`; remote failure must not roll back local saves.

## Size constraints

- Keep the Gradle `dependencies` block empty by default.
- Release builds use `aapt2`, `javac`, `d8`, `zipalign`, and `apksigner` directly, with no dependency resolution step.
- Prefer vector/XML resources and system fonts.
- Do not bundle the PyTorch model in Android. Classification remains an optional server feature until an on-device model has an explicit size and accuracy budget.
- Evaluate APK size on every release and document unexpected growth.

## Storage contract

Database migrations are forward-only. Audio files use app-private storage, so no broad storage permission is needed. Deleting an event must remove its audio file in the same use case. Upgrade tests must confirm database and files survive application updates.

## Release

Source lives in `apps/mobile/android`. `make android-release` writes a versioned, locally installable APK to `apps/mobile/release/android`. Local signing keys and binary artifacts are ignored; production signing credentials remain external.
