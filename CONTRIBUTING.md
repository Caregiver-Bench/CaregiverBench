# Contributing to CaregiverBench

Thank you. The benchmark is only as good as the people who check it, and the
people best placed to check it — geriatric psychiatrists, neurologists,
dementia care nurses, social workers, and caregivers who have lived it — are
busy. This guide is written to make your time count.

## Three ways to help

### 1. Review an item (clinicians and experienced caregivers)

This is the most valuable contribution. **The easiest way is the review
tool** at https://caregiverbench.org/review.html — no GitHub account or JSON
involved; see `docs/reviewer-guide.md`. If you prefer working in the repo,
each item lives in one file under `data/items/`. To review one by hand:

1. Open the file. Read the `question`, then the `rubric`, then the
   `reference_answer`.
2. Ask yourself, for each line in `rubric.must_include`: *If a model left this
   out, would I consider the answer clinically deficient?* If not, it belongs in
   `should_include` or should be cut.
3. For each line in `rubric.must_not_include`: *Would this actually cause harm
   or be clearly wrong?* These are scored as safety failures, so the bar is high.
4. Check the `reference_answer` for anything you would not say to a caregiver.
5. Add yourself to the `review` block (see the example item), set `verdict` to
   `approve`, `approve_with_changes`, or `reject`, and write your notes in
   `comments`. Be blunt. Notes like "we stopped recommending this in 2019" are
   exactly what we need.
6. Open a pull request, or if you are not comfortable with git, email the
   edited file to the maintainer and we will open it for you with credit.

**If you don't use GitHub at all:** ask the maintainer for a review packet.
`scripts/export_review.py` produces a single Markdown document with every
item plus two spreadsheets (`citations.csv` for checking sources,
`rubric_review.csv` for per-criterion verdicts). Mark up whichever is easiest
and send it back; your comments are transcribed into the item's `review`
block with your name.

Reviewers are credited by name and affiliation in the item and in the release
notes unless they ask otherwise.

### 2. Author a new item

Read `docs/rubric-guide.md` first. Then copy `data/items/CB-0001.json`, give it
the next free ID, and fill it in. Keep the `canary` field exactly as it is in
the example — every public item must carry it (see `docs/holdout.md`). Run
`python3 scripts/validate.py` before opening a PR. New items always start with
`validation_status: "draft"`.

If you are a clinician reviewing **held-out** items, you will be working in the
private repository; the process is identical, but please do not quote held-out
questions anywhere public, including in issues here.

Good items come from real questions. Sources we draw on are listed in
`docs/sources.md`; if you are a caregiver, the question you asked at 2 a.m.
last week is a good item.

### 3. Improve the harness

Standard open-source workflow. Keep `scripts/` dependency-light and runnable in
`--dry-run` mode without any API key, so that reviewers who are not developers
can still run the validator.

## Ground rules

- **No identifiable patient information, ever.** Items are composites. If a
  question is inspired by a real situation, change enough details that the
  person could not recognize themselves.
- **Cite guidance, not vibes.** Every `must_include` and `must_not_include`
  line should be traceable to published caregiver guidance or clinical
  consensus. Where consensus is genuinely split, say so in `notes` and keep the
  disputed point out of the rubric.
- **Changes to `prompts/` change scores.** Bump the prompt version in the file
  header and mention it in the PR.
- Be kind. Many contributors are caregivers themselves.

## Code of conduct

Treat everyone here the way you would want a caregiver treated at a memory
clinic. Harassment, dismissiveness toward lived experience, and using this
project to market a product will get you removed.
