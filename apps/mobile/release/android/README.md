# Android releases

Only signed, verified Android delivery artifacts belong here locally. `make android-release` creates:

```text
parrot-care-v<version>.apk
```

APK/AAB files are ignored by Git. Record release version, commit, checksum, signing identity, build command, and verification result in the external release system rather than committing binaries.

Current local release target:

```text
parrot-care-v0.3.0.apk
```

0.2.1 completed basic Android device verification. 0.3.0 adds the first core sound workflow: daily baseline recording and local comparison of loudness, peak level, and sound activity.

Device smoke test:

```bash
apps/mobile/android/scripts/device-smoke-test.sh
```
