# Mobile

Android is the only supported mobile platform.

- `android/`: native Java/XML Android application with no third-party runtime.
- `release/android/`: local APK/AAB delivery directory; binaries are ignored by Git.

Run `make check-android` for architecture checks. The release build uses Android SDK tools directly, matching the small, dependency-free architecture proven in `mistake-notebook`.
