# The Counciler

Kareem's personal AI Council: send an idea from the app or from Slack, the best-suited AI replies with a 1-2-3 plan, and the app shows how much API balance is left and when it runs out.

- **SPEC.md** — the full project spec. Read it before writing any code.
- **design/** — approved UI mockups (Council and Usage screens).
- **CURSOR_PROMPTS.md** — the build steps, one PR each.
- **reseller-programs/** — Agent SDK bot that answers only reseller-program questions (partners by country, line items, quote structure, country prices). Feed via `reseller-programs/feed/*.csv` (`npm run feed`). Use/deploy: `reseller-programs/README.md`, `FEED.md`, `GO_LIVE.md`.
