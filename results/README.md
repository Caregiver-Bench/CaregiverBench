# Results

`runs/` is git-ignored: it holds raw model outputs from local runs. When a
dataset version is released, the runs used for the published numbers are
copied into a versioned folder here (e.g. `v0.2/`) together with their
`scores.json`, so every published figure can be traced to an exact model,
prompt version, judge, and dataset hash.
