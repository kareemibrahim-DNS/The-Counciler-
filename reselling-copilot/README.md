# Reselling Copilot

> **Slack: use the Reselling Brain bot, not this Worker.** The team-wide Slack bot is the Reselling Brain (`kareemibrahim-DNS/orbit-reselling-wizard`, folder `reselling-brain/slack-bot`). It uses the same catalogue (`reselling-brain/catalog` is a copy of `data/` here) plus policy, SLAs and processes, with owner/team layers. This Worker bot (`src/`) is on hold so the team never sees two bots. Keep `data/` and the Brain's `catalog/` in sync (roadmap COP-2).

Quoting assistant for the Foodics Marketplace reselling team: partners, line items, list prices and quote structure, in a web page and in Slack.

> **This repo holds selling data only.** No cost prices, wholesale terms or margins, ever. CI blocks them (`npm run guard`).

## What it does

- **Builds quotes:** partner + country + branches + billing + deal type → exact Salesforce line items, quantities, list prices, totals, structure checks and discount eligibility.
- **Tells partners apart in the same category**, e.g. Grubtech vs Deliverect vs UrbanPiper vs FeedUs, or ShopBrain vs Supy.
- **Works in Slack:** `@Reselling Copilot quote Grubtech for 4 branches, KSA, annual` → reply in the thread.
- **Protects you:** in partner channels (e.g. `#ksa-grubtech`) it only discusses that partner and never shows the discount rules. Unknown shared channels get no pricing. Cost questions are refused before reaching the model.

## Quick start

```bash
npm ci
npm run check        # guard + typecheck + tests
cp .dev.vars.example .dev.vars   # fill in tokens locally
npm run dev
```

Slack setup: [`docs/SLACK_SETUP.md`](docs/SLACK_SETUP.md). Working with AI assistants: [`AGENTS.md`](AGENTS.md) and [`docs/ROADMAP.md`](docs/ROADMAP.md).

## Data sources (5 Nov 2026)

| File | Source |
|---|---|
| `data/catalog.json` | Salesforce Standard Price Book (SAR, AED, KWD, JOD, EGP) + "USD 1 – International", active Marketplace products |
| `data/partners.json` | the old internal price-list sheet Partner Guide + Salesforce product descriptions + Partnerships notes |
| `data/policy.json` | Discount policy (3 Oct 2026) and Reseller Policy 2026 terms |
| `data/channels.json` | Partner Slack channels from the Partner Guide |

## Known data issues

- The the old internal price-list sheet price list doesn't match Salesforce (e.g. Grubtech gOnline Annual 1,311.75 vs 1,421.10 SAR). Its KSA column holds KWD values for Ordable, Zyda and Mnasati. This repo uses Salesforce.
- Six VOLT lines have inconsistent prices across currencies (flagged ⚠ in the data).
- ShopBrain Essential has no main-branch line in Salesforce, only additional-branch lines.
