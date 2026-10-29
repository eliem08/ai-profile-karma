<!-- sell-kit:start -->
# AI Profile Karma

[![CI](https://github.com/eliem08/ai-profile-karma/actions/workflows/ci.yml/badge.svg)](https://github.com/eliem08/ai-profile-karma/actions/workflows/ci.yml)

> **See what AI services know about you, then fix it or delete it.**

**Who it's for:** Privacy-conscious individuals and the families they protect.

**The problem:** Chat exports and AI memories quietly collect your address, health, finances and more, and getting them removed is a chore.

**What you get:** A local scan of your AI exports for personal and sensitive data, an exposure score, and ready-to-send GDPR and CCPA deletion letters.

## Quickstart

Customers receive a release archive with the wheel and the examples. Python 3.10+ and no other dependencies.

```bash
pip install ai_profile_karma-0.1.0-py3-none-any.whl
ai-profile-karma scan README.md
ai-profile-karma letter --vendor "ExampleAI Inc." --law ccpa --action delete --name "Jane Doe" --email jane@example.com
```

## Web app and API

Every command is also a JSON API endpoint and a browser form, served by the built-in web app.

```bash
ai-profile-karma-web --port 8000          # then open http://127.0.0.1:8000
ai-profile-karma-web keys create --label "first customer"   # prints an API key (stored hashed)
docker build -t ai-profile-karma . && docker run -p 8000:8000 -e API_KEYS=sk_... -v ai-profile-karma-data:/data ai-profile-karma
```

Every API call needs `Authorization: Bearer <key>` once any key exists; a server on a public address refuses to start without one. Calls are rate-limited per key (60/min, `--rate`) and metered: `ai-profile-karma-web usage` prints calls per key for billing.

Endpoints: `POST /api/scan`, `POST /api/letter`, plus `GET /healthz` and `GET /api/spec` (machine-readable field list).
Files are sent as `{"name": ..., "content": ...}`, folders as `{"files": [...]}` or a base64 zip.

## Deploy and sell

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/eliem08/ai-profile-karma)

`render.yaml` (one click, above) and `fly.toml` (`fly launch --copy-config`) both run the Dockerfile with a persistent `/data` volume and a `/healthz` check.
To sell self-serve, set four variables and point a Stripe webhook at `https://<your-host>/billing/webhook` (events `checkout.session.completed` and `customer.subscription.deleted`):

| Variable | Example |
|---|---|
| `STRIPE_SECRET_KEY` | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` |
| `STRIPE_PRICES` | `personal=price_123,family=price_456,lifetime=price_789` |
| `STRIPE_ONE_TIME_PLANS` | `lifetime` (one-time checkout, no trial; every other plan is monthly with a 14-day trial) |
| `PUBLIC_URL` | `https://ai-profile-karma.example.com` |

Copy `.env.example` to `.env` and fill in real values; it lists every variable name and nothing else.

Buyers pick a plan on `/pricing`, pay on Stripe Checkout and see their API key once on the success page. Cancelling the subscription revokes the key. A selling server always requires a key.

## Pricing

Monthly plans start with a 14-day free trial. Prices in USD, billed monthly unless noted.
All plans unlock the same software in this release — higher tiers add licence scope, not gated
features. Scan history and re-check reminders are roadmap items, not shipped features.

| Plan | Price | Includes |
|---|---|---|
| **Personal** | $5 per month | Unlimited local scans; Exposure score; Deletion letters |
| **Family** | $12 per month | Everything in Personal; Household licence, up to 6 people |
| **Lifetime** | $79 one-time | Everything in Personal, paid once — Personal plan forever, no subscription |

To start a trial or buy a plan, [request access](https://github.com/eliem08/ai-profile-karma/issues/new?title=AI%20Profile%20Karma%20trial&labels=sales). Lifetime checks out as a one-time payment (no trial) and must be listed in `STRIPE_ONE_TIME_PLANS`, not sold as a subscription.

## Licence

Proprietary. Copyright (c) 2026 eliem08. All rights reserved. Use requires a paid plan or an active trial; see [LICENSE](LICENSE).
<!-- sell-kit:end -->

## What it does

- **Scans exports** you download yourself (ChatGPT `conversations.json`,
  assistant memory dumps, any `.txt / .md / .json`)
- **Detects PII**: emails, phone numbers, street addresses, dates of birth,
  SSN-shaped numbers, payment cards (Luhn-validated), IBANs
- **Infers sensitive categories** (GDPR Art. 9 style): health, finances,
  location, employer, relationships/family, religion, politics, sexuality
- **Exposure score** (0–100) weighted by sensitivity, with evidence snippets
  (masked) so you can see *why*
- **Request letters**: GDPR Art. 15/16/17 or CCPA access / correct / delete,
  pre-filled with the findings

Everything runs locally; nothing is uploaded anywhere.

## Quickstart

```bash
pip install -e .
ai-profile-karma scan ~/Downloads/chatgpt-export/
ai-profile-karma letter --vendor "ExampleAI Inc." --law gdpr --action delete --name "Jane Doe" --email jane@example.com
```

## Roadmap

- Browser extension that pulls exports for you from each assistant
- Continuous monitoring: re-scan monthly, alert on new sensitive facts
- One-click request sending + tracking the 30/45-day response deadlines
- Data-broker coverage (people-search sites feeding AI agents)

## Development

Zero runtime dependencies; Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m unittest discover -s tests -t .           # unit + CLI smoke tests
ruff check . && ruff format --check .               # lint + format
```

```
ai_profile_karma/core.py       domain logic (pure, importable, fully tested)
ai_profile_karma/__main__.py   CLI (`ai-profile-karma ...` / `python -m ai_profile_karma ...`)
tests/                unit tests + generated CLI smoke tests
```

CI runs lint and tests on Ubuntu and Windows across Python 3.10, 3.12 and 3.13.
Design, data model, trade-offs and production path: **[ARCHITECTURE.md](ARCHITECTURE.md)**.

Part of the [agent-economy](https://github.com/eliem08/agent-economy) portfolio (idea #13).
