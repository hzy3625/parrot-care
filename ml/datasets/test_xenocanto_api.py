#!/usr/bin/env python3
"""Test Xeno-Canto API v3 and v2 for parrot recordings."""
import urllib.request
import json
import sys

headers = {"User-Agent": "ParrotCare/0.4 (research)"}

# Try API v3 first
urls = [
    ("v3-psittacidae", "https://xeno-canto.org/api/3/recordings?query=psittacidae&page=1"),
    ("v3-parrot", "https://xeno-canto.org/api/3/recordings?query=parrot&page=1"),
    # Try v2 as fallback
    ("v2-psittacidae", "https://xeno-canto.org/api/2/recordings?query=psittacidae"),
]

for label, url in urls:
    print(f"\n--- {label} ---")
    print(f"URL: {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        print(f"Keys: {list(data.keys())}")
        if "numRecordings" in data:
            print(f"Total recordings: {data['numRecordings']}")
        if "numSpecies" in data:
            print(f"Num species: {data['numSpecies']}")
        if "recordings" in data:
            recs = data["recordings"]
            print(f"Recordings on page: {len(recs)}")
            for r in recs[:3]:
                genus = r.get("gen", "?")
                species = r.get("sp", "?")
                en_name = r.get("en", "?")
                license = r.get("lic", "?")
                file_url = r.get("file", "?")[:80] if r.get("file") else "N/A"
                print(f"  {genus} {species} ({en_name}) | License: {license} | File: {file_url}")
        elif "data" in data:
            d = data["data"]
            if isinstance(d, list):
                print(f"Data items: {len(d)}")
                for r in d[:3]:
                    print(f"  {r.get('gen','?')} {r.get('sp','?')} ({r.get('en','?')}) | License: {r.get('lic','?')}")
            elif isinstance(d, dict):
                print(f"Data keys: {list(d.keys())}")
                for k in ["numRecordings", "numSpecies", "recordings"]:
                    if k in d:
                        print(f"  {k}: {d[k]}")
        else:
            # Print first 500 chars
            print(f"Response (first 500 chars): {json.dumps(data, ensure_ascii=False)[:500]}")
    except Exception as e:
        print(f"Error: {e}")

# Also try searching for specific parrot types
print("\n\n--- Searching for specific parrot behaviors ---")
queries = [
    ("parrot scream", "parrot+scream"),
    ("parrot call", "parrot+call"),
    ("budgerigar", "budgerigar"),
    ("cockatoo scream", "cockatoo+scream"),
]
for label, q in queries:
    url = f"https://xeno-canto.org/api/3/recordings?query={q}&page=1"
    print(f"\n{label}: {url}")
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=20)
        data = json.loads(resp.read())
        if isinstance(data, dict):
            for k in ["numRecordings", "numSpecies"]:
                if k in data:
                    print(f"  {k}: {data[k]}")
            if "recordings" in data:
                print(f"  Recordings: {len(data['recordings'])}")
    except Exception as e:
        print(f"  Error: {e}")
