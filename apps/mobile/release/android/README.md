# Android releases

Only signed, verified Android delivery artifacts belong here locally. `make android-release` creates:

```text
parrot-care-v<version>.apk
```

APK/AAB files are ignored by Git. Record release version, commit, checksum, signing identity, build command, and verification result in the external release system rather than committing binaries.
