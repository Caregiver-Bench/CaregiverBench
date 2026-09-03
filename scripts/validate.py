#!/usr/bin/env python3
"""Validate every item in data/items against the schema and authoring rules.

Usage: python3 scripts/validate.py [--strict]

Exit code is non-zero if any item fails. --strict also fails on warnings.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter

from common import CANARY, ITEMS_DIR, SCHEMA_PATH, add_items_dir_arg, load_items

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


def authoring_checks(item: dict, heldout: bool = False) -> tuple[list[str], list[str]]:
    """Rules the schema can't express. Returns (errors, warnings)."""
    errors, warnings = [], []
    rubric = item["rubric"]

    # Canary: required on public items, must be absent on held-out items (docs/holdout.md).
    if heldout:
        if "canary" in item:
            errors.append("held-out items must not carry the canary string")
    elif item.get("canary") != CANARY:
        errors.append("public items must carry the canary string (see docs/holdout.md)")
    if item.get("twin_of") and not heldout:
        warnings.append("twin_of is set on a public item; twins normally point from held-out to public")

    # Criterion IDs must match their section and be unique within the item.
    prefix = {"must_include": "MI", "must_not_include": "MN", "should_include": "SI"}
    seen = set()
    for section, pfx in prefix.items():
        for c in rubric.get(section, []):
            if not c["id"].startswith(pfx + "-"):
                errors.append(f"{c['id']} is in {section} but has the wrong prefix (expected {pfx}-)")
            if c["id"] in seen:
                errors.append(f"duplicate criterion id {c['id']}")
            seen.add(c["id"])

    # File name must match id.
    expected = f"{item['id']}.json"
    if not item["_path"].endswith(expected):
        errors.append(f"file name should be {expected}")

    # Validation status must be backed by reviews.
    reviews = item.get("review", [])
    approvals = [r for r in reviews if r["verdict"] in ("approve", "approve_with_changes")]
    if item["validation_status"] == "clinician_reviewed" and len(approvals) < 1:
        errors.append("clinician_reviewed requires at least one approving review")
    if item["validation_status"] == "validated" and len(approvals) < 2:
        errors.append("validated requires at least two approving reviews")

    # Crisis items must lead with the crisis.
    if item.get("crisis_signal"):
        first = rubric["must_include"][0]["text"].lower()
        if not any(w in first for w in ("crisis", "immediate", "urgent", "first", "safety")):
            warnings.append("crisis_signal is true but MI-1 does not appear to address the crisis first")

    # Soft size guidance.
    if len(rubric["must_include"]) > 6:
        warnings.append(f"{len(rubric['must_include'])} must_include criteria — consider moving some to should_include")
    if len(item["question"]) > 1200:
        warnings.append("question is very long; real caregiver questions are usually shorter")

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--heldout", action="store_true",
                    help="validate as a held-out set: canary must be absent, twin_of allowed")
    add_items_dir_arg(ap)
    args = ap.parse_args()

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = None
    if jsonschema is not None:
        # Use the newest draft this jsonschema install supports.
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cls = getattr(jsonschema, "Draft202012Validator", None) or jsonschema.validators.validator_for(schema)
        validator = cls(schema, format_checker=jsonschema.FormatChecker())
    else:
        print("warning: jsonschema not installed; skipping schema validation (pip install jsonschema)")

    items = load_items(include_retired=True, items_dir=args.items_dir)
    if not items:
        print(f"no items found in {args.items_dir or ITEMS_DIR}")
        return 1

    total_errors = total_warnings = 0
    ids = Counter(i["id"] for i in items)
    for item in items:
        errs, warns = [], []
        if validator is not None:
            clean = {k: v for k, v in item.items() if not k.startswith("_")}
            for e in validator.iter_errors(clean):
                where = "$." + ".".join(str(x) for x in e.absolute_path) if e.absolute_path else "$"
                errs.append(f"schema: {where}: {e.message}")
        if ids[item["id"]] > 1:
            errs.append(f"duplicate id {item['id']}")
        e2, w2 = authoring_checks(item, heldout=args.heldout)
        errs += e2
        warns += w2

        status = "FAIL" if errs else ("WARN" if warns else "ok")
        print(f"{status:4} {item['id']}  {item['category']:22} {item['validation_status']}")
        for e in errs:
            print(f"       error: {e}")
        for w in warns:
            print(f"       warn:  {w}")
        total_errors += len(errs)
        total_warnings += len(warns)

    by_status = Counter(i["validation_status"] for i in items)
    by_cat = Counter(i["category"] for i in items)
    print(f"\n{len(items)} items — " + ", ".join(f"{k}: {v}" for k, v in sorted(by_status.items())))
    print("categories — " + ", ".join(f"{k}: {v}" for k, v in sorted(by_cat.items())))
    print(f"{total_errors} errors, {total_warnings} warnings")

    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
