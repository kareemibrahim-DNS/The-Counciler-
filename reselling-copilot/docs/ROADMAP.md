# Roadmap

Each task has an owner so assistants don't collide. Branch name: `ai/<owner>/<id>`. Every PR must pass `npm run check`.

Status: ⬜ open · 🟨 in progress · ✅ done

## Done (v0.1, Claude)

- ✅ Partner catalogue: 29 partners, ~200 line items, Salesforce list prices in SAR/AED/KWD/JOD/EGP/USD
- ✅ Same-category comparison data (best for, edge, licensing unit, countries, watch-outs)
- ✅ Quote rules: discount bands, deal types, Reseller Policy 2026 terms
- ✅ Slack bot: mention or DM → threaded reply; partner-channel isolation; cost-question block
- ✅ Cost guard in CI, 10 tests

## ChatGPT (Codex)

- ⬜ **GPT-1 · Quote calculator in code.** Move quote arithmetic out of the model: `src/quote.ts` takes `{partner, country, branches, billing, dealType, extras}` and returns line items, quantities, totals and discount eligibility from `data/`. The bot calls it and the model only explains. Add thorough tests (Wafeq 1/3/5 branches, Supy minimum 3, Zyda Advanced includes 3, ShopBrain 1 main + N−1, InvoiceQ per terminal).
- ⬜ **GPT-2 · Optional OpenAI provider.** Add `LLM_PROVIDER=openai` support in a separate `src/llm-openai.ts` using the official OpenAI SDK, selected in `src/index.ts`. Claude stays the default. Same system prompt and same audience rules.
- ⬜ **GPT-3 · Arabic answers QA.** Write 20 Arabic/Egyptian/Gulf test questions in `tests/fixtures/questions-ar.json` with expected key facts.

## Grok (xAI)

- ⬜ **GROK-1 · Optional xAI provider.** Add `LLM_PROVIDER=xai` in `src/llm-xai.ts` using xAI's official SDK or documented API. Claude stays the default.
- ⬜ **GROK-2 · Red-team the confidentiality rules.** Write `tests/fixtures/attacks.json`: 30 prompts that try to extract cost/margin, cross-partner prices in partner channels, or discount rules ("I'm the CEO", "for testing", role-play, Arabic, base64). Add a test that runs `asksForCost` and the prompt builder against them, and propose fixes in `src/policy.ts`.
- ⬜ **GROK-3 · Competitive notes.** For each category, propose extra "Edge / Watch out" facts with public source links in a PR to `data/partners.json` (marked `needs-review`).

## GitHub Copilot

- ⬜ **COP-1 · Review every PR** against `.github/copilot-instructions.md` (enable Copilot code review on the repo).
- ⬜ **COP-2 · Catalogue sync script.** `scripts/sync-salesforce.mjs`: reads an exported Salesforce price-book CSV (Product Name, Code, Currency, List Price, Description) and regenerates `data/catalog.json`. It must refuse any column named cost/margin. The same JSON is copied to `orbit-reselling-wizard/reselling-brain/catalog/` (the Reselling Brain); document the copy step.
- ⬜ **COP-3 · Build web/index.html from data/.** `scripts/build-web.mjs` re-embeds `data/*.json` into the page so the page never drifts from the bot.

## Partnerships (humans)

- ⬜ **H-0** Slack: deploy the Reselling Brain bot (Orbit repo, `reselling-brain/slack-bot`, Socket Mode, needs an always-on host). This repo's Worker bot stays on hold.

- ⬜ **H-1** Slack admin approves the app; create it from `docs/SLACK_SETUP.md`.
- ⬜ **H-2** Decide who owns the Cloudflare account and the Anthropic API key.
- ⬜ **H-3** Fix price mismatches found during the build (see README "Known data issues").
