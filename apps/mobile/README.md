# Mobile

Android is the only supported mobile platform.

- `android/`: native Java/XML Android application with no third-party runtime; current version is `0.3.1`.
- `release/android/`: local APK/AAB delivery directory; binaries are ignored by Git.

Current product flow: record daily baselines, record or import an observation, compare it locally with recent baselines, and retain the result context in the local record library. The launcher icon combines a parrot and sound waves to represent that purpose.

Run `make check-android` for architecture checks. The release build uses Android SDK tools directly, matching the small, dependency-free architecture proven in `mistake-notebook`.
