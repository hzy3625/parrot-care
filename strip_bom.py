# Remove BOM from readme.md and re-encode cleanly
with open("readme.md", "rb") as f:
    data = f.read()

# Strip UTF-8 BOM if present
if data[:3] == b'\xef\xbb\xbf':
    data = data[3:]

# Decode as UTF-8 and re-encode without BOM
text = data.decode('utf-8')

# Write back without BOM
with open("readme.md", "wb") as f:
    f.write(text.encode('utf-8'))

print(f"File size: {len(text.encode('utf-8'))} bytes (no BOM)")
print(f"Title: {text.split(chr(10))[0]}")
