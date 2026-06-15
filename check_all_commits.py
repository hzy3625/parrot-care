import subprocess

# Check bytes in each commit
commits = {
    "2fddfdb (original)": "2fddfdb:readme.md",
    "1f781a9 (corrupted)": "1f781a9:readme.md",
    "951c740 (revert)": "951c740:readme.md",
    "673f9c6 (current fix)": "673f9c6:readme.md",
}

expected_title = "# ParrotCare AI - \u9e66\u9e49\u5065\u5eb7\u884c\u4e3a\u76d1\u6d4b\u7cfb\u7edf"

for label, ref in commits.items():
    try:
        result = subprocess.run(
            ["git", "cat-file", "blob", ref],
            capture_output=True, check=True
        )
        blob = result.stdout
        if blob[:3] == b'\xef\xbb\xbf':
            blob = blob[3:]
        text = blob.decode('utf-8')
        line1 = text.split('\n')[0]
        match = line1 == expected_title
        print(f"{label}: {len(blob)} bytes, Title match: {match}")
        if not match:
            print(f"  Got: {repr(line1)}")
    except Exception as e:
        print(f"{label}: ERROR - {e}")
