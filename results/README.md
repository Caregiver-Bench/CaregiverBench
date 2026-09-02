# Results

`runs/` is git-ignored: it holds raw model outputs from local runs. When a
dataset version is released, the runs used for the published numbers are
copied into a versioned folder here (e.g. `v0.2/`) together with their
`scores.json`, so every published figure can be traced to an exact model,
prompt version, judge, and dataset hash.

For held-out runs, only `scores.json` (aggregates) and the held-out
`*.manifest.json` (content hash) are published here. `responses.jsonl` and
`judgments.jsonl` from held-out runs must never be committed.
