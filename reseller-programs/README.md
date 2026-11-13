# Reseller Programs Agent

Agent SDK bot that answers **only** reseller-program questions:

1. Available partners (filtered by country)
2. Available line items
3. Commercial + Operational quote structure per partner
4. Line-item price for a given country
5. Which partners operate in which countries

## Catalog

Authoritative data lives in `bot/lib/catalog.ts` (SAMPLE rows until you replace them). Tools never invent partners or prices outside that file.

## Local loop

```bash
cd reseller-programs
npx --yes "@grok/agent-sdk@0.6.0" validate --dir .
npx --yes "@grok/agent-sdk@0.6.0" tool call list_partners --dir . --input '{"country":"SA"}'
npx --yes "@grok/agent-sdk@0.6.0" run --dir . --message "Which partners work in SA?"
npx --yes "@grok/agent-sdk@0.6.0" dev
npm run check
```

## Deploy

See the Agent SDK deploy skill / `npx @grok/agent-sdk deploy --dir . --dry-run` after you are signed in. Do not deploy from CI without saving the alias token securely.
