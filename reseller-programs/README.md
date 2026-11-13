# Reseller Programs Agent

Agent SDK bot that answers **only** reseller-program questions:

1. Available partners (filtered by country)
2. Available line items
3. Commercial + Operational quote structure per partner
4. Line-item price for a given country
5. Which partners operate in which countries

## Where we are

| Item | Status |
| --- | --- |
| Code | On `main` / feature branches under `reseller-programs/` |
| Behavior | Reseller-only; refuses off-topic |
| Tools | `list_partners`, `list_line_items`, `get_quote_structure`, `get_line_item_price` |
| Data | Fed from [`feed/*.csv`](feed/) → [`bot/lib/catalog.data.ts`](bot/lib/catalog.data.ts) |
| Current feed | Real Ballurh SA commercials from partner email; other Foodics pipeline partners listed with commercial/ops **Not loaded** until Orbit/contract rows are pasted |
| Deploy | See [`GO_LIVE.md`](GO_LIVE.md) — you run `deploy` |

```text
You ask → agent → catalog tools → feed/*.csv (via catalog.data.ts) → answer or refuse
```

## How to use

### Local playground

```bash
cd reseller-programs
npx --yes "@grok/agent-sdk@0.6.0" login
npx --yes "@grok/agent-sdk@0.6.0" dev
```

Open the playground URL. Try:

- `Which partners are available in SA?`
- `What is the quote structure for Ballurh?`
- `What is the Ballurh Subscription Base price in SA?`
- `Write a poem` → should refuse

### One-shot CLI

```bash
npx --yes "@grok/agent-sdk@0.6.0" run --dir . --message "Which partners work in SA?"
```

### Tool-only smoke (no model login)

```bash
npx --yes "@grok/agent-sdk@0.6.0" tool call list_partners --dir . --input '{"country":"SA"}'
npx --yes "@grok/agent-sdk@0.6.0" tool call get_line_item_price --dir . --input '{"lineItemName":"Ballurh Subscription Base","country":"SA"}'
```

### Hosted

Follow [`GO_LIVE.md`](GO_LIVE.md).

## How to feed

See [`FEED.md`](FEED.md). Short version:

1. Edit `feed/partners.csv`, `feed/line_items.csv`, `feed/prices.csv` (or paste Orbit export in chat).
2. `npm run feed && npm run check`
3. Validate / playground / deploy

## Scripts

```bash
npm run feed    # rebuild catalog.data.ts from feed/*.csv
npm run check   # tsc --noEmit
npm run dev     # agent-sdk dev
```
