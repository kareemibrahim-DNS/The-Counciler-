# Reselling Copilot

> **Slack: use the Reselling Brain bot, not this Worker.** The reseller bot is the Reselling Brain in this repo (`reselling-brain/slack-bot`, deployed on Railway). It uses the same catalogue (`reselling-brain/catalog` is a copy of `data/` here) plus policy, flows and cycles, with layers. This Worker bot (`src/`) is on hold so the team never sees two bots. Keep `data/` and `reselling-brain/catalog/` in sync (roadmap COP-2). Never change `orbit-reselling-wizard` from this repo's work.

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

## Data sources (prices refreshed 14 Nov 2026)

| File | Source |
|---|---|
| `data/catalog.json` | Salesforce Standard Price Book (SAR, AED, KWD, JOD, EGP) + "USD 1 – International", active Marketplace products |
| `data/partners.json` | the old internal price-list sheet Partner Guide + Salesforce product descriptions + Partnerships notes |
| `data/policy.json` | Discount policy (3 Oct 2026) and Reseller Policy 2026 terms |
| `data/channels.json` | Partner Slack channels from the Partner Guide |

## Refreshing prices from Salesforce
`node scripts/refresh-prices.mjs <result.json>…` updates the list prices in `data/catalog.json` from saved PricebookEntry query results (the SOQL is at the top of the script). It never adds or removes lines; it reports new and missing products, and flags lines whose currencies differ by 2× or more. Then copy `data/catalog.json` to `reselling-brain/catalog/`, run `npm run feed:salesforce` in `reseller-programs/` and `python build_sales_skill.py` in `reselling-brain/slack-bot/`.

## Known data issues

- The the old internal price-list sheet price list doesn't match Salesforce (e.g. Grubtech gOnline Annual 1,311.75 vs 1,421.10 SAR). Its KSA column holds KWD values for Ordable, Zyda and Mnasati. This repo uses Salesforce.
- Eight VOLT lines have inconsistent prices across currencies (flagged ⚠ in the data), e.g. VOLT Hosting with SAP [Monthly] is USD 5,000 but SAR 1,750.
- ShopBrain Essential has no main-branch line in Salesforce, only additional-branch lines.
