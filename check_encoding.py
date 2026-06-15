with open("readme.md", "rb") as f:
    data = f.read()

text_bytes = data[3:]  # Skip BOM
text = text_bytes.decode("utf-8")
lines = text.split("\n")

# Check line 1 carefully
line1 = lines[0]
expected = "# ParrotCare AI - 鹦鹉健康行为监测系统"
print(f"Line 1 length: {len(line1)}")
print(f"Expected length: {len(expected)}")
print(f"Chars in line 1 beyond expected:")
if len(line1) > len(expected):
    for i in range(len(expected), len(line1)):
        c = line1[i]
        print(f"  pos {i}: U+{ord(c):04X} ({repr(c)})")
elif len(line1) < len(expected):
    for i in range(len(line1), len(expected)):
        c = expected[i]
        print(f"  missing at pos {i}: U+{ord(c):04X} ({repr(c)})")

# Check individual character codes
print(f"\nLine 1 char codes (after 'ParrotCare AI - '):")
start = 18
for i in range(start, min(len(line1), start+20)):
    c = line1[i]
    print(f"  {i}: U+{ord(c):04X}")

print(f"\nExpected char codes (after 'ParrotCare AI - '):")
for i in range(start, min(len(expected), start+20)):
    c = expected[i]
    print(f"  {i}: U+{ord(c):04X}")

# Full comparison
same = True
for i in range(max(len(line1), len(expected))):
    c1 = line1[i] if i < len(line1) else None
    c2 = expected[i] if i < len(expected) else None
    if c1 != c2:
        print(f"\nDIFF at pos {i}: line1={repr(c1)}(U+{ord(c1):04X}) expected={repr(c2)}(U+{ord(c2):04X})")
        same = False
print(f"\nAll chars match: {same}")

# Also check for invisible chars
print(f"Line 1 repr: {repr(line1)}")
print(f"Expected repr: {repr(expected)}")
