# Instructions for AI agents (ChatGPT / Codex, Grok, GitHub Copilot, Claude)

This repo is worked on by several AI assistants plus the Foodics Partnerships team. Read this file fully before changing anything.

## What this is

**Reselling Copilot** helps the Foodics Marketplace reselling team build quotes for partner apps (Grubtech, Deliverect, ShopBrain, BrandWallet, ...):

- `web/index.html`: a self-contained page (partner catalogue, same-category comparison, quote rules, chat).
- `src/`: a Slack bot (Cloudflare Worker). Mention it in a channel or DM it; it replies in the thread using Claude.
- `data/`: the single source of truth: line items + **list prices** from the Salesforce price book, partner profiles, categories, discount policy, and the Slack channel → partner map.

## Golden rules (non-negotiable)

1. **Selling data only.** Never add cost price, buy price, wholesale price, margin, markup, partner payout or commission, not in `data/`, `web/`, prompts, tests, fixtures, comments or commit messages. `npm run guard` and CI enforce this. Do not weaken or bypass the guard.
2. **Partner channels are partner-only.** In channels listed in `data/channels.json` partner staff can read replies. The bot must only talk about that one partner and must never show the internal discount policy there. Keep `tests/bot.test.ts` passing; add a test whenever you touch `src/policy.ts` or `src/prompt.ts`.
3. **No secrets in git.** Tokens and API keys go in Wrangler secrets (`npx wrangler secret put ...`) or `.dev.vars` (ignored).
4. **Exact Salesforce names.** Line-item names in `data/catalog.json` must match Salesforce exactly. Don't rename, translate or "fix" them.
5. **Don't invent data.** If a price, partner or rule is missing, leave it missing and open an issue tagged `needs-data`.
6. **Small PRs.** One task per PR, with `npm run check` passing. Describe what you changed and how you tested it.

## Commands

```bash
npm ci
npm run check      # guard + typecheck + tests (must pass before every PR)
npm run dev        # local Worker (needs .dev.vars, see .dev.vars.example)
npm run deploy     # Partnerships only
```

## Layout

| Path | Purpose |
|---|---|
| `src/index.ts` | Slack Events endpoint, ack < 3s, reply in thread |
| `src/policy.ts` | Who can read the reply (internal / partner / external) + cost-question block |
| `src/prompt.ts` | System prompt + catalogue slicing (only relevant partners are sent, for speed) |
| `src/llm.ts` | Claude call (official `@anthropic-ai/sdk`) |
| `src/slack.ts` | Signature verification + Slack Web API |
| `data/*.json` | Catalogue, partners, categories, policy, channel map |
| `web/index.html` | Stand-alone page with the same data embedded |
| `docs/ROADMAP.md` | Open tasks and which assistant picks them up |
| `scripts/export-grok-feed.mjs` | Regenerates `../reseller-programs/feed/*.csv` (the Grok Agent SDK bot) from `data/`. Edit `data/`, never the CSVs. Only signed resellers are exported. |

## How assistants split the work

See `docs/ROADMAP.md`. Pick a task assigned to you, open a branch `ai/<assistant>/<task-id>`, and open a PR. If you disagree with a task, say so in the PR. Don't silently change scope.
