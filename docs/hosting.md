# Hosting: caregiverbench.org on Cloudflare Workers

The site is static: `site/index.html` (landing page), `site/how-it-works.html`
(methods and plan), `site/review.html` (the review tool), and `site/data/`
(the compiled dataset, generated at build time and git-ignored). It is served
by Cloudflare Workers as static assets, deployed from a laptop with Wrangler,
and the review tool is gated with Cloudflare Access so only listed reviewers
can open it. All of this is on Cloudflare's free tiers. The domain is
registered with Cloudflare, so DNS needs no manual work.

Cloudflare Pages would also work, but Cloudflare now points new projects at
Workers and has stopped adding features to Pages, so Workers is the choice.
If the review tool later needs a server-side endpoint (see *Later*), it is
added to this same Worker.

## Deploying

`wrangler.toml` at the repository root is the whole configuration. Wrangler
needs Node.js; `npx` fetches it on demand.

```bash
npx wrangler login              # once; opens a browser to authorize
python3 scripts/build_site.py   # validates items, compiles data into site/data/
npx wrangler deploy             # uploads site/ and serves it at caregiverbench.org
```

`build_site.py` runs the validator first and exits non-zero if any item is
invalid, so a broken item can never be published: `&&` the two commands. The
first deploy also creates the DNS record and certificate for
`caregiverbench.org` (the `routes` entry with `custom_domain = true`); it is
usually live within a minute. Every later deploy is the same two commands.
`workers_dev` and `preview_urls` are off so the site exists only at the custom
domain, which is the only hostname Access can gate.

There is no git integration: deploys happen from a checkout, so `main` on
GitHub and the live site can differ until someone deploys. Deploy after
merging item changes.

## Gating the review tool with Cloudflare Access

Cloudflare dashboard → **Zero Trust**. The first visit asks for a team name
(any name; it only appears on the login page) and a plan; the Free plan
covers up to 50 users. Cloudflare may ask for a payment method on file even
for the Free plan; nothing is charged.

**Settings → Authentication → Login methods**: confirm **One-time PIN** is
listed (it is on by default). That is all reviewers need: they enter their
email and get a code. Nobody creates an account.

**Access → Applications → Add an application → Self-hosted**:

| Field | Value |
|---|---|
| Application name | CaregiverBench review |
| Session duration | 1 week (reviewers come back over several days) |
| Public hostname | domain `caregiverbench.org`, path `review*` |

`review*` covers `review.html` and any future `review/` routes. Leave the
landing pages and `data/*` ungated: the dataset is CC BY 4.0 and the tool
fetches it.

**Policy**: name `Reviewers`, action **Allow**, include rule **Emails** with
the reviewers' addresses, one per line. To add a reviewer later, edit this
list; to remove one, delete the email and, under **Access → Users**, revoke
their session. A second include rule, **Emails ending in**, admits everyone
at a partner institution's domain if that is ever wanted.

Visiting `caregiverbench.org/review.html` now shows Cloudflare's login page;
after the code is entered, the tool loads. Check that `caregiverbench.org/`
and `caregiverbench.org/how-it-works.html` still open without a login.

## What reviewers see

Send them `https://caregiverbench.org/review.html` and
`docs/reviewer-guide.md` (or its contents in an email). Their work is saved in
their browser as they go; when done they press **Export review**, which
downloads a small JSON file they email to the maintainer. Apply it with:

```bash
python3 scripts/apply_review.py reviews/review-jane-doe-2026-09-10.json
python3 scripts/validate.py
git add -A && git commit -m "Apply review from Jane Doe"
python3 scripts/build_site.py && npx wrangler deploy
```

## Later: removing the email step

When "email me the file" becomes annoying, add a fetch handler to the Worker
(`src/index.js`, ~40 lines, plus a `main` line in `wrangler.toml`) that
accepts the exported bundle with a POST and writes it to a KV namespace or D1
table. Because the request passes through Access, the
`Cf-Access-Authenticated-User-Email` header identifies the reviewer reliably,
so the name field in the tool becomes cosmetic. The bundle format does not
change; `apply_review.py` reads the same JSON whether it came by email or was
pulled from KV.

## Held-out items

Do not deploy held-out items to the site, even behind Access. The review tool
works from a file on a laptop (open `review.html` and pick the JSONL when
prompted), which is how held-out review should happen until there is a reason
to change the threat model. See `docs/holdout.md`.
