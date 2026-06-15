import subprocess, sys

result = subprocess.run(["git", "cat-file", "blob", "HEAD:readme.md"], capture_output=True)
blob = result.stdout

# Strip BOM if present
if blob[:3] == b'\xef\xbb\xbf':
    blob = blob[3:]

text = blob.decode('utf-8')
lines = text.split('\n')

expected_title = "# ParrotCare AI - \u9e66\u9e49\u5065\u5eb7\u884c\u4e3a\u76d1\u6d4b\u7cfb\u7edf"
expected_line3 = "## MVP V0.1 \u9a8c\u8bc1\u7248"

print(f"Title: '{lines[0]}'")
print(f"Title matches expected: {lines[0] == expected_title}")
print(f"Line 3: '{lines[2]}'")
print(f"Line 3 matches expected: {lines[2] == expected_line3}")

# Count CJK
import re
cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
repl = text.count('\ufffd')
qm = text.count('?')
print(f"CJK: {cjk}, Replacements: {repl}, Question marks: {qm}")

# Show all lines with CJK
print(f"\nAll lines with CJK:")
for i, line in enumerate(lines):
    chars = re.findall(r'[\u4e00-\u9fff]', line)
    if chars:
        print(f"  L{i+1}: {''.join(chars)} ({len(chars)} chars)")
