#!/usr/bin/env python3
"""
REQ-019: Xeno-Canto Data Download Script

Downloads parrot/psittacidae recordings from Xeno-Canto API v3.
Filters by Creative Commons license (CC-BY, CC-BY-SA for commercial safety).

Usage:
    python scripts/download_xenocanto_data.py --api-key YOUR_KEY --max-per-class 50
    python scripts/download_xenocanto_data.py --api-key YOUR_KEY --query "Psittacidae" --output data/audio/

Requirements:
    pip install requests tqdm
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# Xeno-Canto API v3
API_BASE = "https://xeno-canto.org/api/3/recordings"

# License filters - only download commercially-safe licenses
SAFE_LICENSES = {
    "CC-BY 4.0",       # Attribution only
    "CC-BY-SA 4.0",    # Attribution-ShareAlike
    "CC-BY 3.0",
    "CC-BY-SA 3.0",
}

# All CC licenses (including non-commercial)
ALL_CC_LICENSES = SAFE_LICENSES | {
    "CC-BY-NC 4.0",
    "CC-BY-NC-SA 4.0",
    "CC-BY-NC 3.0",
    "CC-BY-NC-SA 3.0",
}

# ParrotCare category mapping
# Xeno-Canto doesn't have our exact categories, but we can map some
CATEGORY_MAPPING = {
    # normal_chirp: parrot calls/songs
    "normal_chirp": {
        "queries": [
            "Psittacidae type:call",
            "Psittacidae type:song",
            "parrot call",
            "budgerigar call",
            "cockatiel call",
        ],
        "max_per_query": 50,
    },
    # scream: parrot alarm/aggressive calls
    "scream": {
        "queries": [
            "Psittacidae type:alarm",
            "Psittacidae type:aggressive",
            "cockatoo scream",
            "parrot alarm call",
        ],
        "max_per_query": 30,
    },
    # night_fright, plucking, silence: not available on Xeno-Canto
    # These require real-world recording
}


def search_recordings(query: str, api_key: str, page: int = 1) -> dict:
    """Search Xeno-Canto recordings via API v3."""
    url = f"{API_BASE}?query={urllib.parse.quote(query)}&page={page}"
    headers = {
        "User-Agent": "ParrotCare/0.4 (research)",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, headers=headers)
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())


def download_file(url: str, filepath: str, retries: int = 3) -> bool:
    """Download a file with retry logic."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ParrotCare/0.4"})
            resp = urllib.request.urlopen(req, timeout=60)
            with open(filepath, "wb") as f:
                f.write(resp.read())
            return True
        except Exception as e:
            print(f"  Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(2)
    return False


def filter_by_license(recordings: list, commercial_only: bool = True) -> list:
    """Filter recordings by license type."""
    allowed = SAFE_LICENSES if commercial_only else ALL_CC_LICENSES
    filtered = []
    for rec in recordings:
        lic = rec.get("lic", "")
        if lic in allowed:
            filtered.append(rec)
    return filtered


def download_category(category: str, config: dict, api_key: str,
                      output_dir: str, max_per_class: int,
                      commercial_only: bool = True) -> int:
    """Download recordings for a specific ParrotCare category."""
    cat_dir = os.path.join(output_dir, category)
    os.makedirs(cat_dir, exist_ok=True)

    total_downloaded = 0
    metadata = []

    for query in config["queries"]:
        if total_downloaded >= max_per_class:
            break

        print(f"\nSearching: '{query}' for '{category}'")
        try:
            data = search_recordings(query, api_key)
        except urllib.error.HTTPError as e:
            print(f"  API error: {e.code} {e.reason}")
            if e.code == 401:
                print("  ⚠️  API key invalid or missing. Get one at https://xeno-canto.org")
                return -1
            continue
        except Exception as e:
            print(f"  Error: {e}")
            continue

        num_recordings = data.get("numRecordings", "unknown")
        recordings = data.get("recordings", [])
        print(f"  Found {num_recordings} total recordings, {len(recordings)} on this page")

        # Filter by license
        filtered = filter_by_license(recordings, commercial_only)
        print(f"  After license filter: {len(filtered)} recordings")

        for rec in filtered:
            if total_downloaded >= max_per_class:
                break

            file_url = rec.get("file")
            if not file_url or file_url == "None":
                continue

            # Generate filename
            rec_id = rec.get("id", "unknown")
            genus = rec.get("gen", "unknown")
            species = rec.get("sp", "unknown")
            filename = f"{category}_{rec_id}_{genus}_{species}.mp3"
            filepath = os.path.join(cat_dir, filename)

            if os.path.exists(filepath):
                print(f"  Skip (exists): {filename}")
                continue

            print(f"  Downloading: {filename}")
            if download_file(file_url, filepath):
                total_downloaded += 1
                metadata.append({
                    "filename": filename,
                    "category": category,
                    "xeno_canto_id": rec_id,
                    "species": f"{genus} {species}",
                    "english_name": rec.get("en", ""),
                    "license": rec.get("lic", ""),
                    "recordist": rec.get("rec", ""),
                    "country": rec.get("cnt", ""),
                    "url": rec.get("url", ""),
                })
                time.sleep(1)  # Rate limit: 1 second between downloads
            else:
                print(f"  Failed to download: {filename}")

    # Save metadata
    if metadata:
        meta_path = os.path.join(cat_dir, "_xenocanto_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"\nMetadata saved: {meta_path}")

    return total_downloaded


def main():
    parser = argparse.ArgumentParser(description="Download parrot sounds from Xeno-Canto")
    parser.add_argument("--api-key", required=True, help="Xeno-Canto API Key (v3)")
    parser.add_argument("--output", default="data/audio", help="Output directory")
    parser.add_argument("--max-per-class", type=int, default=50, help="Max recordings per category")
    parser.add_argument("--commercial-only", action="store_true", default=True,
                        help="Only download CC-BY/CC-BY-SA (commercial-safe)")
    parser.add_argument("--allow-nc", action="store_true",
                        help="Include CC-BY-NC recordings (non-commercial)")
    parser.add_argument("--category", choices=list(CATEGORY_MAPPING.keys()),
                        help="Download specific category only")
    args = parser.parse_args()

    commercial_only = not args.allow_nc
    categories = {args.category: CATEGORY_MAPPING[args.category]} if args.category else CATEGORY_MAPPING

    print("=" * 60)
    print("ParrotCare - Xeno-Canto Data Downloader")
    print("=" * 60)
    print(f"Output: {args.output}")
    print(f"Max per class: {args.max_per_class}")
    print(f"License filter: {'CC-BY/CC-BY-SA only (commercial-safe)' if commercial_only else 'All CC licenses'}")
    print()

    total = 0
    for category, config in categories.items():
        print(f"\n{'='*40}")
        print(f"Category: {category}")
        print(f"{'='*40}")

        count = download_category(
            category, config, args.api_key,
            args.output, args.max_per_class, commercial_only
        )

        if count == -1:
            print("\n❌ API key error. Aborting.")
            sys.exit(1)

        print(f"\nDownloaded {count} recordings for '{category}'")
        total += count

    print(f"\n{'='*60}")
    print(f"Total downloaded: {total} recordings")
    print(f"{'='*60}")

    if total > 0:
        print("\nNext steps:")
        print("1. Run feature extraction:")
        print("   python scripts/batch_extract_features.py --input-dir data/audio --output data/training_data.csv")
        print("2. Retrain model:")
        print("   python backend/train_model.py --epochs 50 --model-path models/audio_classifier.pt")

    # Print attribution notice
    print("\n⚠️  ATTRIBUTION NOTICE:")
    print("All recordings sourced from Xeno-Canto (https://xeno-canto.org)")
    print("See _xenocanto_metadata.json in each category directory for")
    print("individual recording attributions and license information.")
    print("You MUST include these attributions in your project.")


if __name__ == "__main__":
    import urllib.parse  # needed for quote()
    main()
