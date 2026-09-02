#!/usr/bin/env python3
"""Compile data/items/*.json into data/build/caregiverbench.jsonl.

Retired items are excluded. A small manifest with counts and a content hash is
written alongside so results can be tied to an exact dataset version.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date

from common import BUILD_DIR, load_items, write_jsonl


def main() -> None:
    items = load_items()
    rows = [{k: v for k, v in i.items() if not k.startswith("_")} for i in items]
    out = BUILD_DIR / "caregiverbench.jsonl"
    write_jsonl(out, rows)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()[:16]
    manifest = {
        "built": date.today().isoformat(),
        "items": len(rows),
        "sha256_16": digest,
        "by_status": dict(Counter(r["validation_status"] for r in rows)),
        "by_category": dict(Counter(r["category"] for r in rows)),
    }
    (BUILD_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(BUILD_DIR.parent.parent)} ({len(rows)} items, hash {digest})")


if __name__ == "__main__":
    main()
