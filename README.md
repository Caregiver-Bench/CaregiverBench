# CaregiverBench

**An open benchmark for evaluating how well AI models answer the questions dementia caregivers actually ask.**

Status: pre-alpha. Schema and harness are in place and there are 30 draft items, three per category. None has been clinically validated yet. Nothing here should be used to make care decisions.

## Why this should exist

### The problem

Nearly 13 million Americans provide unpaid care for someone living with dementia, and a growing share of them turn to AI chatbots for help at 2 a.m. when no nurse line is open. The questions they ask are hard: they mix medical facts, behavioral strategy, safety, ethics, and the caregiver's own exhaustion. A response that sounds confident and reasonable can still be wrong in ways that matter — recommending reality orientation for someone who asks to "go home," suggesting an antihistamine for sleep, or missing the signal that a caregiver is in crisis.

Nobody currently measures this. The published studies of chatbot answers to caregiver questions are small (dozens of questions), graded by hand by a few clinicians, cover one model at one point in time, and cannot be re-run when the next model ships. Their conclusions — broadly reassuring on general information, weaker on clinical specifics and on anticipating what comes next — are useful, but they are snapshots, not an instrument. Meanwhile the models change every few months, and the products built on them (including the small open-weight models that end up in low-cost caregiving apps) are shipped without any domain-specific safety evidence at all.

### Why existing benchmarks don't cover it

General medical QA benchmarks test recall of textbook facts against a single correct answer. Caregiver questions rarely have one. The right answer depends on who is asking, on which stage of the disease, and on noticing what the question doesn't say; the failure modes are omissions and confidently harmful suggestions rather than factual errors. Scoring that needs a rubric — what a clinically sound answer *must* say, *must not* say, and *should* say — written and checked by people who do this work, and a scoring method that rewards substantive help rather than a reflexive "ask your doctor." None of the existing public benchmarks provide that for dementia care, and the structure here is general enough to be copied for other caregiving domains.

### What the research community gets

**A clinician-validated dataset, openly licensed.** Every item is a realistic question with a persona, a reference answer, a three-tier rubric, cited sources, a difficulty rating, and a visible validation status with reviewer provenance. The data is CC BY 4.0, so it can be reused for evaluation, fine-tuning, product QA, or as seed material for other benchmarks.

**A reproducible measurement instrument, not a leaderboard screenshot.** The harness records the exact model string, prompt version, dataset hash, sample count, and error count for every run, publishes 95% bootstrap confidence intervals, and reports paired comparisons so that small differences are called "not distinguishable" rather than ranked. The goal is that anyone with API keys can rerun a release and get the same numbers.

**Diagnostic output, not just a score.** Beyond the headline number, each release reports the safety pass rate, per-category and per-difficulty breakdowns, crisis items separately, the deflection rate, and — usually the most useful part — a table of which `must_not_include` lines each model trips. That is the information a model developer or a product team can act on.

**A validated LLM judge, with the validation data published.** Before any release the judge is calibrated against two clinicians on a stratified sample of graded answers, and the judge–clinician and clinician–clinician agreement figures (Cohen's κ per criterion type) are published. That corpus of clinician-graded (item, answer) pairs is itself a rare artifact for anyone studying LLM-as-judge in a clinical domain.

**A contamination-aware design that others can copy.** A private held-out set with a published content hash, item "twins" split across the public and held-out pools to make training-set leakage measurable, a canary string in every data file, and a rotation scheme that keeps the development set fresh. Small clinical benchmarks are especially vulnerable to contamination; this is a worked example of how to build one anyway.

**Coverage of the models people actually deploy.** The roster deliberately includes open-weight models at several sizes and small (~7–9B) models alongside the frontier APIs, so the results speak to the question builders in aging care actually face: how much safety do you give up for cost.

### Who it is for

Researchers studying AI in health and aging, who need a standing measure rather than a one-off study. Model developers, who need to know what their models get wrong in this domain before a caregiver finds out. Teams building caregiver-facing products, who need evidence for the model choice they are making. Clinicians and caregiver advocates, who deserve a public, independent answer to "is it safe to ask a chatbot this?" that no vendor gets to write for itself.

## What it measures

Each item is a realistic caregiver question paired with a **reference answer** and a **rubric**: the specific things a clinically sound answer must include, must not include, and should include when it can. Models are scored against the rubric, not against the prose of the reference answer, so there is no single "right" wording.

Rubrics are written so that a clinician can review them in minutes, and so that both human graders and an LLM judge can apply them consistently. Every item carries a `validation_status` so the community can see exactly which items have been through clinical review and which are still drafts.

Categories cover the full span of the caregiving arc — see [`docs/taxonomy.md`](docs/taxonomy.md).

## Repository layout

```
data/items/         One JSON file per benchmark item (easy to review in a PR)
data/build/         Compiled JSONL dataset, generated by scripts/build_dataset.py
schema/             JSON Schema that every item must satisfy
scripts/            Validation, model runner, judge, and dataset build
prompts/            System and judge prompts (versioned — changes affect scores)
docs/               Taxonomy, rubric authoring guide, sources, held-out set design, roadmap
results/            Model outputs and scores (committed per release, not per run)
site/               caregiverbench.org: landing page and the browser-based review tool
reviews/            Review bundles exported from the tool and applied to items (provenance)
```

## Quick start

```bash
python3 -m pip install -r requirements.txt

# Check every item against the schema and authoring rules
python3 scripts/validate.py

# Compile items into a single JSONL file
python3 scripts/build_dataset.py

# Run a model against the dataset (dry-run needs no API key; release runs use --samples 3)
python3 scripts/run_eval.py --model dry-run --samples 3
# e.g. --model anthropic:<model>, openai:<model>, openrouter:meta-llama/<model>

# Score the responses against each item's rubric (dry-run needs no API key)
python3 scripts/judge.py --run results/runs/<run-id> --judge dry-run

# Export a review packet (Markdown + CSVs) for reviewers who don't use GitHub
python3 scripts/export_review.py

# Build the website (validates, compiles the dataset, copies it under site/data/)
python3 scripts/build_site.py

# Apply a review bundle exported from the review tool
python3 scripts/apply_review.py reviews/review-jane-doe-2026-09-10.json
```

Real runs need `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and/or `OPENROUTER_API_KEY` in the environment. See `scripts/run_eval.py --help`. Every script accepts `--items-dir` to run against a held-out checkout instead of `data/items/`.

## How models are evaluated

Every model in the roster gets each question once, cold: a minimal neutral system prompt, no tools, no retrieval, no conversation history, three samples at the model's default temperature. An LLM judge applies the rubric line by line and returns a verdict with evidence for each criterion, plus a flag for answers that only deflect ("ask your doctor"). Item score is the mean over samples; run score is the mean over items with a 95% bootstrap confidence interval. The judge is a different model family from the one under test, and it is not trusted until its verdicts have been compared with two clinicians' grades on a stratified sample and the agreement published. Until that has happened for a dataset version, its numbers are labelled judge-unvalidated.

The roster covers frontier API models (Anthropic, OpenAI, Google), open-weight models at several sizes (Llama, Qwen, Mistral, Gemma, DeepSeek) through one hosting provider, and small models explicitly, since those are what end up in low-cost products. Results report the headline score next to the safety pass rate, per-category and per-difficulty breakdowns, crisis items separately, the deflection rate, and, most usefully, which must-not lines each model trips. No score is ever self-reported: every published number comes from a run of this harness whose manifests are committed in `results/`.

The full protocol, including judge validation, statistics, contamination monitoring, and the release checklist, is in [`docs/evaluation.md`](docs/evaluation.md).

## How items are validated

1. **Draft** — authored from published caregiver guidance (see `docs/sources.md`), rubric written, passes `validate.py`.
2. **Clinician reviewed** — at least one dementia-care clinician has reviewed the question, reference answer, and rubric and signed off in the item's `review` block.
3. **Validated** — reviewed by two independent clinicians with disagreements resolved and documented.

Only *validated* items count toward the headline score. Draft and reviewed items are reported separately.

## Held-out set

This repository is the public development set. A separate **held-out set**, kept in a private repository under the `Caregiver-Bench` GitHub organization and authored to the same standard, will become the headline score once it is large enough. Held-out results are published only as aggregates, together with a content hash of the exact dataset used, so released items can later be verified. Every public data file carries a canary string so vendors can filter it from training corpora. Details, including rotation and contamination twins, are in [`docs/holdout.md`](docs/holdout.md).

## Reviewing items without touching JSON

`site/review.html` is a single-file, dependency-free web tool for reviewers. It shows each item with its rubric and sources, lets the reviewer edit text in place (changes are tracked, not applied), record a verdict on every rubric line, check every citation, and give an overall verdict with comments. Work is saved in the browser; **Export review** produces a small JSON bundle that the maintainer applies with `scripts/apply_review.py`, which shows each proposed change as a diff, records the review in the item, and promotes `validation_status` when the rules are met. The tool is hosted at caregiverbench.org behind an email allow-list (see [`docs/hosting.md`](docs/hosting.md)) and also works opened from a laptop. Reviewer instructions are in [`docs/reviewer-guide.md`](docs/reviewer-guide.md).

## Contributing

We especially need clinicians, social workers, and experienced caregivers to review items. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

Code is released under the [MIT License](LICENSE). The dataset (everything under `data/` and `prompts/`) is released under [CC BY 4.0](DATA_LICENSE). See [`CITATION.cff`](CITATION.cff) for how to cite.

## Maintainer

Rich Curtis · [caregiverbench.org](https://caregiverbench.org) · rich@caregiverbench.org
