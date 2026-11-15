# GitHub Copilot instructions

Applies to `reselling-copilot/`. Follow `reselling-copilot/AGENTS.md`.

- This repo holds **selling (list) prices only**. Never suggest code, data or tests containing cost price, wholesale price, margin, markup, payout or commission. `npm run guard` fails the build if you do.
- In Slack channels listed in `reselling-copilot/data/channels.json`, the bot answers about that one partner only and never shows the internal discount policy.
- Keep Salesforce line-item names exactly as they are in `reselling-copilot/data/catalog.json`.
- Run `npm run check` before proposing a change. Add a test when you touch `reselling-copilot/src/policy.ts` or `reselling-copilot/src/prompt.ts`.
- When reviewing PRs, flag any change that could leak one partner's pricing to another partner or expose discount rules in a partner channel.
- The reseller bot is `reselling-brain/` in this repo. Never propose changes to `orbit-reselling-wizard` (Orbit) as part of this work.
