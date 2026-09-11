# Roadmap

## v0.1 — "Something to react to"
- [x] Repo, schema, harness skeleton
- [x] 30 draft items, three per category (citations verified against live pages; clinical review pending)
- [x] Dry-run of harness end to end
- [x] Review packet export for reviewers without GitHub
- [x] Browser review tool (site/review.html) + apply_review.py; hosting on Cloudflare Workers + Access documented
- [x] Site deployed at caregiverbench.org with Access allow-list
- [ ] Clinical review process agreed with an academic partner
- [x] Held-out set design documented (`docs/holdout.md`); harness supports `--items-dir`
- [x] Evaluation protocol documented (`docs/evaluation.md`); harness supports samples, OpenRouter, deflection flag, bootstrap CIs

## v0.2 — First validated set
- [ ] 50+ items, at least 30 validated by two clinicians
- [ ] Judge validation: 100 stratified (item, answer) pairs graded by two clinicians; κ published (docs/evaluation.md §4)
- [ ] Release run of the full roster (frontier + open-weight + small) with --samples 3; results in `results/v0.2/` with CIs, trigger table, deflection rate

## v1.0 — Public release
- [ ] 100+ validated items
- [ ] Private held-out repository created under the `Caregiver-Bench` org; ~40 validated items, ~25% with public twins
- [ ] Held-out manifest hash published with results; headline score switches to held-out
- [ ] Leaderboard on caregiverbench.org
- [ ] Methods write-up
