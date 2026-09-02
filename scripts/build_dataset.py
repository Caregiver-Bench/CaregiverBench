#!/usr/bin/env python3
"""Compile data/items/*.json into data/build/caregiverbench.jsonl.

Usage: python3 scripts/build_dataset.py [--items-dir DIR] [--name NAME]

For a held-out checkout, pass --items-dir and a --name such as heldout-v1; the
resulting manifest.json is what gets committed publicly with the scores.

Retired items are excluded. A small manifest with counts and a content hash is
written alongside so results can be tied to an exact dataset version.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import date

from common import BUILD_DIR, add_items_dir_arg, load_items, write_jsonl


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="caregiverbench", help="dataset name used for output files")
    add_items_dir_arg(ap)
    args = ap.parse_args()

    items = load_items(items_dir=args.items_dir)
    rows = [{k: v for k, v in i.items() if not k.startswith("_")} for i in items]
    out = BUILD_DIR / f"{args.name}.jsonl"
    write_jsonl(out, rows)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
    manifest = {
        "name": args.name,
        "built": date.today().isoformat(),
        "items": len(rows),
        "sha256_16": digest,
        "by_status": dict(Counter(r["validation_status"] for r in rows)),
        "by_category": dict(Counter(r["category"] for r in rows)),
    }
    (BUILD_DIR / f"{args.name}.manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(BUILD_DIR.parent.parent)} ({len(rows)} items, hash {digest})")


if __name__ == "__main__":
    main()
