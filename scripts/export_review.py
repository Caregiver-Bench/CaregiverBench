#!/usr/bin/env python3
"""Export items as a review packet for people who don't use GitHub.

Usage:
  python3 scripts/export_review.py                 # all items -> review/
  python3 scripts/export_review.py --category safety end_of_life
  python3 scripts/export_review.py --status draft --out /tmp/packet

Writes:
  <out>/items.md          Every item in reading order: question, reference answer,
                          rubric, sources, notes. Open in any Markdown viewer or
                          paste into a doc.
  <out>/citations.csv     One row per (item, source) with blank columns for the
                          reviewer's verdict and notes. Open in Excel/Numbers.
  <out>/rubric_review.csv One row per rubric criterion with blank verdict columns.

Held-out packets: pass --items-dir; the packet is then marked CONFIDENTIAL.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from common import ROOT, add_items_dir_arg, load_items

CATEGORY_ORDER = [
    "communication", "behavioral_symptoms", "daily_care", "safety", "medical",
    "stages_and_prognosis", "caregiver_wellbeing", "legal_financial",
    "care_transitions", "end_of_life",
]


def md_item(it: dict) -> str:
    a = it["asker"]
    who = f"{a['relationship'].replace('_', ' ')}, {a['setting'].replace('_', ' ')}"
    if a.get("person_stage"):
        who += f"; person: {a['person_stage']} stage"
    if a.get("dementia_type") and a["dementia_type"] != "unspecified":
        who += f", {a['dementia_type'].replace('_', ' ')}"
    out = [f"## {it['id']} — {it['category'].replace('_', ' ')}",
           "",
           f"*Difficulty {it['difficulty']} · {it['validation_status']} · asker: {who}"
           + (" · **CRISIS SIGNAL**" if it.get("crisis_signal") else "") + "*",
           f"*Tags: {', '.join(it.get('tags', []))}*", "",
           "### Question", "", "> " + it["question"].replace("\n", "\n> "), "",
           "### Reference answer", "", it["reference_answer"], "",
           "### Rubric", ""]
    for section, label in (("must_include", "Must include"), ("must_not_include", "Must NOT include"), ("should_include", "Should include")):
        crits = it["rubric"].get(section, [])
        if not crits:
            continue
        out.append(f"**{label}**")
        out.append("")
        for c in crits:
            line = f"- **{c['id']}** {c['text']}"
            if c.get("rationale"):
                line += f"  \n  *Rationale: {c['rationale']}*"
            out.append(line)
        out.append("")
    out += ["### Sources", ""]
    for s in it["sources"]:
        yr = f" ({s['year']})" if s.get("year") else ""
        url = f" — <{s['url']}>" if s.get("url") else ""
        out.append(f"- {s['title']}, {s.get('publisher', '')}{yr}{url}")
    out += ["", "### Author notes", "", it.get("notes", "—"), ""]
    if it.get("review"):
        out += ["### Reviews", ""]
        for r in it["review"]:
            out.append(f"- {r['date']} — {r['reviewer']} ({r.get('credentials', '')}, {r.get('affiliation', '')}): **{r['verdict']}**. {r.get('comments', '')}")
        out.append("")
    out += ["---", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "review")
    ap.add_argument("--category", nargs="*", default=None)
    ap.add_argument("--status", nargs="*", default=None)
    add_items_dir_arg(ap)
    args = ap.parse_args()

    items = load_items(items_dir=args.items_dir)
    if args.category:
        items = [i for i in items if i["category"] in args.category]
    if args.status:
        items = [i for i in items if i["validation_status"] in args.status]
    items.sort(key=lambda i: (CATEGORY_ORDER.index(i["category"]), i["id"]))
    if not items:
        raise SystemExit("no items match")

    args.out.mkdir(parents=True, exist_ok=True)
    heldout = bool(args.items_dir)

    # items.md
    head = ["# CaregiverBench review packet", "",
            f"Generated {date.today().isoformat()} · {len(items)} items · "
            + ", ".join(f"{c.replace('_', ' ')}: {sum(1 for i in items if i['category'] == c)}" for c in CATEGORY_ORDER if any(i['category'] == c for i in items)),
            ""]
    if heldout:
        head += ["**CONFIDENTIAL — held-out items. Do not share, quote, or upload.**", ""]
    head += ["How to review: read the question, then the rubric, then the reference answer. "
             "For each *must include* line ask whether omitting it would make an answer clinically deficient; "
             "for each *must not include* line ask whether it would actually cause harm. "
             "Record verdicts in `rubric_review.csv` and citation checks in `citations.csv`, or just mark up this document.", "",
             "Contents: " + " · ".join(i["id"] for i in items), "", "---", ""]
    (args.out / "items.md").write_text("\n".join(head) + "\n".join(md_item(i) for i in items), encoding="utf-8")

    # citations.csv
    with (args.out / "citations.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "category", "source_title", "publisher", "year", "url",
                    "supports_claim", "url_resolves (Y/N)", "content_supports (Y/N/partial)", "reviewer", "notes"])
        for it in items:
            for s in it["sources"]:
                w.writerow([it["id"], it["category"], s["title"], s.get("publisher", ""), s.get("year", ""), s.get("url", ""),
                            "", "", "", "", ""])

    # rubric_review.csv
    with (args.out / "rubric_review.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["item_id", "category", "criterion_id", "section", "text", "rationale",
                    "verdict (keep/edit/move/drop)", "suggested_edit", "reviewer"])
        for it in items:
            for section in ("must_include", "must_not_include", "should_include"):
                for c in it["rubric"].get(section, []):
                    w.writerow([it["id"], it["category"], c["id"], section, c["text"], c.get("rationale", ""), "", "", ""])

    n_src = sum(len(i["sources"]) for i in items)
    print(f"wrote {args.out}/items.md, citations.csv ({n_src} rows), rubric_review.csv  [{len(items)} items]")


if __name__ == "__main__":
    main()
