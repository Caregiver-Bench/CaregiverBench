# Hosting: caregiverbench.org on Cloudflare Pages

The site is static: `site/index.html` (public landing page), `site/review.html`
(the review tool), and `site/data/` (the compiled dataset, generated at build
time). It is deployed with Cloudflare Pages, and the review tool is gated with
Cloudflare Access so only listed reviewers can open it. Both are free at this
scale. The domain is already registered with Cloudflare, so DNS needs no work.

## 1. Connect the repository to Cloudflare Pages (once)

Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** →
**Connect to Git** → choose the `CaregiverBench` repository.

Build settings:

| Setting | Value |
|---|---|
| Production branch | `main` |
| Build command | `pip3 install jsonschema && python3 scripts/build_site.py` |
| Build output directory | `site` |

The build runs the validator first, so a broken item fails the deploy rather
than publishing. The default Pages build image includes Python 3; if a build
log complains about the version, set the environment variable
`PYTHON_VERSION` to `3.11` in the project settings. The `pip3 install`
gives the validator full schema checking during the build.

Every push to `main` redeploys. Pull requests get preview URLs automatically.

## 2. Custom domain

In the Pages project → **Custom domains** → **Set up a custom domain** →
`caregiverbench.org`. Because the zone is on Cloudflare, the DNS record is
created for you; it is usually live within a minute. Add `www.caregiverbench.org`
the same way if you want it to redirect.

## 3. Gate the review tool with Cloudflare Access

Cloudflare dashboard → **Zero Trust** (first visit asks you to pick a team
name; the free plan is fine).

**Settings → Authentication → Login methods**: make sure **One-time PIN** is
enabled. That is all reviewers need: they enter their email and get a code.
Nobody has to create an account.

**Access → Applications → Add an application → Self-hosted**:

| Field | Value |
|---|---|
| Application name | CaregiverBench review |
| Session duration | 1 week (reviewers will come back over several days) |
| Application domain | `caregiverbench.org`, path `review.html` |

Add a second domain entry on the same application: `caregiverbench.org`, path
`review*` — this covers `review.html` and any future `review/` routes. Leave
`data/*` ungated: the public dataset is CC BY 4.0 anyway, and the tool needs
to fetch it.

**Policy**: name `Reviewers`, action **Allow**, include rule **Emails** with the
reviewers' addresses (one per line). To add a reviewer later, edit this list;
to remove one, delete the email and, under **Access → Users**, revoke their
session. Optionally add a second include rule **Emails ending in** for a
partner institution's domain if you want everyone there to have access.

That's it. Visiting `caregiverbench.org/review.html` now shows Cloudflare's
login page; after the code is entered, the tool loads.

## 4. What reviewers see

Send them `https://caregiverbench.org/review.html` and `docs/reviewer-guide.md`
(or just its contents in an email). Their work is saved in their browser as
they go; when done they press **Export review**, which downloads a small JSON
file they email to you. Apply it with:

```bash
python3 scripts/apply_review.py reviews/review-jane-doe-2026-09-10.json
python3 scripts/validate.py
git add -A && git commit -m "Apply review from Jane Doe"
```

## Later: removing the email step

When the "email me the file" step becomes annoying, add a Pages Function
(`functions/api/review.js`, ~40 lines) that accepts the exported bundle with a
POST and writes it to a KV namespace or D1 table. Because the request passes
through Access, the `Cf-Access-Authenticated-User-Email` header identifies the
reviewer reliably, so the name field in the tool becomes cosmetic. The bundle
format does not change; `apply_review.py` reads the same JSON whether it came
by email or was pulled from KV.

## Held-out items

Do not deploy held-out items to the public site, even behind Access. The
review tool works from a file on a laptop (open `review.html` and pick the
JSONL when prompted), which is how held-out review should happen until there
is a reason to change the threat model. See `docs/holdout.md`.
