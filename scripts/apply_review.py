#!/usr/bin/env python3
"""Apply a review bundle exported from site/review.html to the item files.

Usage:
  python3 scripts/apply_review.py reviews/review-jane-doe-2026-09-10.json            # interactive
  python3 scripts/apply_review.py bundle.json --dry-run                               # show only
  python3 scripts/apply_review.py bundle.json --accept-all                            # no prompts
  python3 scripts/apply_review.py bundle.json --items-dir ../caregiverbench-heldout/data/items

For each item in the bundle this script:
  1. shows each proposed text edit as a diff and asks whether to apply it
     (question, reference answer, rubric criterion text);
  2. applies criterion verdicts: 'drop' removes the criterion, 'move' moves it to
     another section (re-numbering IDs), 'edit' is handled by the text diff;
  3. appends a review entry (reviewer, credentials, affiliation, date, verdict,
     comments + a citation-check summary) to the item's `review` array;
  4. promotes validation_status when the ladder rules are met
     (1 approving review -> clinician_reviewed, 2 -> validated).

Nothing is written in --dry-run. Always run validate.py afterwards. Keep the
bundle in reviews/ for provenance; that folder is committed.
"""
from __future__ import annotations

import argparse
import difflib
import json
import sys
from datetime import date
from pathlib import Path

from common import ITEMS_DIR, add_items_dir_arg

PREFIX = {"must_include": "MI", "must_not_include": "MN", "should_include": "SI"}


def ask(prompt: str, auto: bool | None) -> bool:
    if auto is not None:
        return auto
    while True:
        a = input(f"{prompt} [y/n/q] ").strip().lower()
        if a in ("y", "yes"):
            return True
        if a in ("n", "no"):
            return False
        if a in ("q", "quit"):
            raise SystemExit("aborted; nothing written")


def show_diff(label: str, old: str, new: str) -> None:
    print(f"\n--- {label}")
    for line in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=1):
        if line.startswith(("---", "+++")):
            continue
        print("   " + line)


def find_crit(item: dict, cid: str):
    for section, crits in item["rubric"].items():
        for i, c in enumerate(crits):
            if c["id"] == cid:
                return section, i
    return None, None


def renumber(item: dict) -> dict[str, str]:
    """Re-number criterion IDs after drops/moves. Returns old->new map."""
    mapping = {}
    for section, pfx in PREFIX.items():
        for n, c in enumerate(item["rubric"].get(section, []), 1):
            new = f"{pfx}-{n}"
            if c["id"] != new:
                mapping[c["id"]] = new
                c["id"] = new
    return mapping


def apply_item(item: dict, rev: dict, reviewer: dict, auto: bool | None, dry: bool) -> bool:
    changed = False
    print(f"\n==== {item['id']}  ({item['category']}, {item['validation_status']})  verdict: {rev.get('verdict') or '—'}")
    if rev.get("comments"):
        print("   comments: " + rev["comments"].replace("\n", "\n             "))

    # 1. text edits
    for e in rev.get("edits", []):
        path, proposed = e["path"], e["proposed"]
        if path == "question":
            cur = item["question"]
        elif path == "reference_answer":
            cur = item["reference_answer"]
        elif path.startswith("rubric."):
            _, section, cid, _ = path.split(".", 3)
            s, i = find_crit(item, cid)
            cur = item["rubric"][s][i]["text"] if s else None
        else:
            cur = None
        if cur is None:
            print(f"   skip edit to unknown field {path}")
            continue
        if cur != e.get("original", cur):
            print(f"   note: {path} has changed since the reviewer saw it; diff is against the current text")
        show_diff(path, cur, proposed)
        if ask("   apply this edit?", auto):
            if path == "question":
                item["question"] = proposed
            elif path == "reference_answer":
                item["reference_answer"] = proposed
            else:
                item["rubric"][s][i]["text"] = proposed
            changed = True

    # 2. criterion verdicts (drops and moves)
    drops, moves = [], []
    for c in rev.get("criteria", []):
        if c["verdict"] == "drop":
            drops.append(c["id"])
        elif c["verdict"] == "move" and c.get("move_to"):
            moves.append((c["id"], c["move_to"]))
    for cid in drops:
        s, i = find_crit(item, cid)
        if s is None:
            continue
        print(f"\n   DROP {cid}: {item['rubric'][s][i]['text']}")
        if ask("   drop it?", auto):
            item["rubric"][s].pop(i)
            changed = True
    for cid, target in moves:
        s, i = find_crit(item, cid)
        if s is None or target == s:
            continue
        print(f"\n   MOVE {cid} -> {target}: {item['rubric'][s][i]['text']}")
        if ask("   move it?", auto):
            crit = item["rubric"][s].pop(i)
            item["rubric"].setdefault(target, []).append(crit)
            changed = True
    if changed:
        mapping = renumber(item)
        if mapping:
            print("   renumbered: " + ", ".join(f"{a}->{b}" for a, b in mapping.items()))

    # 3. review entry
    if rev.get("verdict"):
        src_notes = []
        for s in rev.get("sources", []):
            flags = []
            if not s.get("resolves"):
                flags.append("link not confirmed")
            if not s.get("supports"):
                flags.append("does not clearly support rubric")
            if s.get("note"):
                flags.append(s["note"])
            if flags:
                src_notes.append(f"source #{s['index'] + 1}: " + "; ".join(flags))
        n_checked = len(rev.get("sources", []))
        n_ok = sum(1 for s in rev.get("sources", []) if s.get("resolves") and s.get("supports"))
        summary = rev.get("comments", "").strip()
        if n_checked:
            summary += f"\nCitations checked: {n_ok}/{n_checked} confirmed." + ("" if not src_notes else " " + " | ".join(src_notes))
        crit_summary = ", ".join(f"{c['id']}:{c['verdict']}" for c in rev.get("criteria", []))
        if crit_summary:
            summary += f"\nCriteria: {crit_summary}"
        entry = {
            "reviewer": reviewer.get("name", "unknown"),
            "credentials": reviewer.get("credentials", ""),
            "affiliation": reviewer.get("affiliation", ""),
            "date": date.today().isoformat(),
            "verdict": rev["verdict"],
            "comments": summary.strip(),
        }
        item.setdefault("review", []).append(entry)
        changed = True

        # 4. promotion
        approvals = [r for r in item["review"] if r["verdict"] in ("approve", "approve_with_changes")]
        old = item["validation_status"]
        if old == "draft" and len(approvals) >= 1:
            item["validation_status"] = "clinician_reviewed"
        if item["validation_status"] == "clinician_reviewed" and len(approvals) >= 2:
            item["validation_status"] = "validated"
        if item["validation_status"] != old:
            print(f"   status: {old} -> {item['validation_status']}")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--accept-all", action="store_true", help="apply every proposed change without asking")
    add_items_dir_arg(ap)
    args = ap.parse_args()

    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    reviewer = bundle.get("reviewer", {})
    items_dir = Path(args.items_dir) if args.items_dir else ITEMS_DIR
    auto = True if args.accept_all else (False if args.dry_run else None)
    print(f"bundle from {reviewer.get('name', '?')} ({reviewer.get('credentials', '')}, {reviewer.get('affiliation', '')}) "
          f"exported {bundle.get('exported', '?')} against dataset {bundle.get('dataset_hash', '?')}; {len(bundle['items'])} items")

    touched = 0
    for rev in bundle["items"]:
        path = items_dir / f"{rev['item_id']}.json"
        if not path.exists():
            print(f"\n==== {rev['item_id']}: file not found, skipping")
            continue
        item = json.loads(path.read_text(encoding="utf-8"))
        if apply_item(item, rev, reviewer, auto, args.dry_run) and not args.dry_run:
            path.write_text(json.dumps(item, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            touched += 1
    print(f"\n{'would update' if args.dry_run else 'updated'} {touched} item file(s). Run scripts/validate.py next.")


if __name__ == "__main__":
    main()
