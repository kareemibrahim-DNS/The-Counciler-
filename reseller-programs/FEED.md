# How to feed the reseller agent

Authoritative catalog = CSV files under `feed/`. Tools never invent rows outside that feed.

## Files

| File | Columns |
| --- | --- |
| [`feed/partners.csv`](feed/partners.csv) | id, name, countries (`SA\|AE`), nature, billing_model, payment_terms, discount_policy, commercial_notes, fulfillment, support_model, sla, operational_notes |
| [`feed/line_items.csv`](feed/line_items.csv) | id, name, description, unit |
| [`feed/prices.csv`](feed/prices.csv) | line_item_id, country, currency, amount |

Countries are ISO 3166-1 alpha-2. One price row per country — never reuse another country’s amount.

## Rebuild

```bash
cd reseller-programs
npm run feed
npm run check
npx --yes "@grok/agent-sdk@0.6.0" validate --dir .
```

`npm run feed` regenerates [`bot/lib/catalog.data.ts`](bot/lib/catalog.data.ts).

## Paste into chat (minimum)

Partner line:

`Grubtech | SA | billing… | payment… | fulfillment… | support… | SLA…`

Price line:

`Grubtech - gOnline License [Annual] | SA | SAR | 1421.1`

Then ask the agent to update the CSVs and run `npm run feed`.

## Orbit export

1. Export Partners + Line Items (+ price sheet when available) from Orbit.
2. Map columns into the three CSVs above (or paste here and ask for a rebuild).
3. Leave `Not loaded` commercial/ops cells until the contract/Orbit row is real — do not invent.
