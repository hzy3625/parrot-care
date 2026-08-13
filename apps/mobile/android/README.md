# Native Android

Minimal Android SDK application for the local-first mobile workflow:

- Java 17, XML Views, platform `Activity`;
- `SQLiteOpenHelper` plus app-private audio files;
- `MediaRecorder` for local AAC recording;
- `MediaPlayer` for local playback;
- local parrot profiles, audio/manual records, recording timer, basic import validation, filters, detail editing, and ZIP backup/import;
- no external dependencies or cross-platform runtime;
- direct Android SDK build with no dependency download step.

Prerequisites: JDK 17, Android SDK 35, and Build Tools 35.0.0.

```bash
make android-release
```

The build calls `aapt2`, `javac`, `d8`, `zipalign`, and `apksigner` directly. It produces an installable, locally signed APK under `../release/android`. The generated local keystore stays under ignored `android/build/`; production signing remains external.

With a USB-debugging device connected:

```bash
apps/mobile/android/scripts/device-smoke-test.sh
```

This installs the latest local release APK, launches the app, and prints recent app logs. Manual verification is still required for recording, importing, editing, deleting, and backup restore flows.
