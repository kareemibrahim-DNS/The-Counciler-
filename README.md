# The Counciler

## The Foodics Reseller Bot lives here
**`reselling-brain/`** is the reseller bot: the Slack bot (deployed on Railway) with layers (everyone, team, manager, cost, owner), mention triggers and hand-offs to Kareem, Hatem and Althurayyaa; the knowledge files; the Salesforce list-price catalogue; and the common-layer skill for @Claude in Slack. Start at `reselling-brain/README.md`.
Nothing is synced to Orbit (`orbit-reselling-wizard`); never change Orbit from this repo's work.

## Also in this repo
Kareem's personal AI Council: send an idea from the app or from Slack, the best-suited AI replies with a 1-2-3 plan, and the app shows how much API balance is left and when it runs out.

- **SPEC.md** — the full project spec. Read it before writing any code.
- **design/** — approved UI mockups (Council and Usage screens).
- **CURSOR_PROMPTS.md** — the build steps, one PR each.
- **reseller-programs/** — Agent SDK bot that answers only reseller-program questions (partners by country, line items, quote structure, country prices). Feed via `reseller-programs/feed/*.csv` (`npm run feed`). Use/deploy: `reseller-programs/README.md`, `FEED.md`, `GO_LIVE.md`.
- **reselling-copilot/** — Slack bot + web page for Marketplace quotes: Salesforce list prices for 29 partners (~200 line items), same-category comparisons, quote rules, partner-channel isolation. Selling data only; CI blocks cost/margin data. Start at `reselling-copilot/AGENTS.md`.
- **reselling-brain/** — the Reselling Brain Slack bot (deployed on Railway, root directory `reselling-brain`): team/sales knowledge, catalogue, owner/team/sales layers. Owner-only knowledge is not in this repo; it comes from a Railway secret.
