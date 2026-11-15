# Reseller Bot web surface (built in Orbit, kept here)

These files are the web version of the reseller bot that was built inside Orbit. They are kept here so everything from this project lives in The-Counciler-. **Nothing here changes Orbit, and nothing is synced back.**

| File | What it is |
| --- | --- |
| `public/reselling-brain.html`, `.css`, `.js` | The "Ask the Reselling Brain" page: a chat box with the answer level shown |
| `functions/api/brain.js` | `POST /api/brain`: checks who is asking, applies a daily limit, runs the Claude tool loop |
| `functions/_lib/reselling-brain.js` | Levels (owner, team, sales), the system prompt and the Claude tool loop |
| `functions/_lib/reselling-brain-tools.js` | `brain_catalog` (list prices, quote structure, comparisons) plus read-only Orbit data tools (partners, ARR, tickets) |
| `scripts/build-brain-knowledge.mjs` | Builds the knowledge and catalogue modules from `../knowledge` and `../catalog`; fails on any cost, margin or markup field |
| `tests/orbit-reselling-brain.test.js` | The tests from Orbit (owner values replaced by placeholders) |
| `docs/RESELLING-BRAIN.md` | How it was set up in Orbit |

## Status
- **Reference only.** These are Cloudflare Pages Functions written for Orbit. They depend on Orbit's sign-in (`getContext`, `levelFor`) and its database, so they don't run on their own here.
- **Generated modules are not copied.** In Orbit they held the owner files. This repo's `knowledge/` and `catalog/` now hold the common layer only (base and sales), so a rebuild from here gives the common layer. The team files (policy, discount eligibility, ARR and churn, SLAs, processes, partner notes) are in the Railway secret with the owner files.
- **The live bot is `../slack-bot/`** on Railway, with the full layers (everyone, team, manager, cost, owner).
- **Only the common layer is in this repo:** team files (policy, discounts, SLAs, processes, partner notes and channels) and owner data (cost and markups, contracts, targets, contacts, trackers) are in the Railway secret `BRAIN_OWNER_KNOWLEDGE_B64`.

To run this web page outside Orbit, it needs its own sign-in and host (for example Cloudflare Pages with Cloudflare Access). Ask Claude to port it when you want it.
