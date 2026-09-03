#!/usr/bin/env python3
"""Assemble the static site: compile the dataset and copy it under site/data/.

Usage: python3 scripts/build_site.py [--items-dir DIR]

This is the Cloudflare Pages build command (output directory: site). It runs
validate.py first and fails the build if any item is invalid, so a broken item
can never be published. site/data/ is git-ignored.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from common import BUILD_DIR, ROOT, add_items_dir_arg

SITE = ROOT / "site"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    add_items_dir_arg(ap)
    args = ap.parse_args()
    extra = ["--items-dir", str(args.items_dir)] if args.items_dir else []

    py = sys.executable
    subprocess.run([py, str(ROOT / "scripts" / "validate.py"), *extra], check=True)
    subprocess.run([py, str(ROOT / "scripts" / "build_dataset.py"), *extra], check=True)

    out = SITE / "data"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("caregiverbench.jsonl", "caregiverbench.manifest.json"):
        shutil.copy2(BUILD_DIR / name, out / name)
    print(f"site ready: {SITE.relative_to(ROOT)}/ (index.html, review.html, data/)")


if __name__ == "__main__":
    main()
