#!/usr/bin/env python3
"""Send every benchmark question to a model and store the raw responses.

Usage:
  python3 scripts/run_eval.py --model dry-run
  python3 scripts/run_eval.py --model anthropic:claude-sonnet-4-5 --samples 3
  python3 scripts/run_eval.py --model openrouter:meta-llama/llama-3.3-70b-instruct --samples 3
  python3 scripts/run_eval.py --model openai:gpt-4o --status validated --limit 10

Release runs use --samples 3 at the model's default temperature (see
docs/evaluation.md). Each run writes results/runs/<run-id>/responses.jsonl
(one row per item per sample) plus run.json describing exactly what was run so
it can be reproduced. Judge the run afterwards with scripts/judge.py.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone

from common import RESULTS_DIR, add_items_dir_arg, load_items, load_prompt, write_jsonl
from providers import make_provider


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def call_with_retries(fn, tries: int = 3):
    """Retry API errors with backoff; content (refusals etc.) is never retried."""
    last = None
    for attempt in range(tries):
        try:
            return fn(), None, attempt
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 ** attempt)
    return "", last, tries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="'dry-run' or '<provider>:<model>'")
    ap.add_argument("--samples", type=int, default=1, help="responses per item (release runs: 3)")
    ap.add_argument("--temperature", type=float, default=None, help="omit to use the model's default")
    ap.add_argument("--status", nargs="*", default=None,
                    help="only items with these validation statuses (default: all non-retired)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--sleep", type=float, default=0.0, help="seconds between calls (rate limiting)")
    add_items_dir_arg(ap)
    args = ap.parse_args()

    items = load_items(items_dir=args.items_dir)
    if args.status:
        items = [i for i in items if i["validation_status"] in args.status]
    if args.limit:
        items = items[: args.limit]
    if not items:
        raise SystemExit("no items match")

    system_prompt, prompt_version = load_prompt("system_prompt")
    provider = make_provider(args.model)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{stamp}-{slug(args.model)}" + ("-heldout" if args.items_dir else "")
    run_dir = RESULTS_DIR / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    rows, retries = [], 0
    total = len(items) * args.samples
    n = 0
    for item in items:
        for s in range(args.samples):
            n += 1
            t0 = time.time()
            answer, error, attempts = call_with_retries(
                lambda: provider.complete(system_prompt, item["question"], max_tokens=args.max_tokens, temperature=args.temperature)
            )
            retries += attempts if error else attempts
            rows.append({
                "item_id": item["id"],
                "sample": s,
                "category": item["category"],
                "validation_status": item["validation_status"],
                "model": args.model,
                "answer": answer,
                "error": error,
                "latency_s": round(time.time() - t0, 2),
            })
            print(f"[{n}/{total}] {item['id']} s{s} {'ERROR ' + error if error else 'ok'}")
            if args.sleep:
                time.sleep(args.sleep)

    write_jsonl(run_dir / "responses.jsonl", rows)
    (run_dir / "run.json").write_text(json.dumps({
        "run_id": run_id,
        "model": args.model,
        "date": stamp[:8],
        "system_prompt_version": prompt_version,
        "items": len(items),
        "samples": args.samples,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
        "responses": len(rows),
        "errors": sum(1 for r in rows if r["error"]),
        "api_retries": retries,
        "status_filter": args.status,
        "items_dir": str(args.items_dir) if args.items_dir else "data/items",
        "heldout": bool(args.items_dir),
        "started": stamp,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {run_dir.relative_to(RESULTS_DIR.parent)}")


if __name__ == "__main__":
    main()
