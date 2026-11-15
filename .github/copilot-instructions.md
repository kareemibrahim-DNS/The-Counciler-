# GitHub Copilot instructions

Applies to `reselling-copilot/`. Follow `reselling-copilot/AGENTS.md`.

- This repo holds **selling (list) prices only**. Never suggest code, data or tests containing cost price, wholesale price, margin, markup, payout or commission. `npm run guard` fails the build if you do.
- Partner Slack channels (`#ksa-…`, `#uae-…`, `#egypt-…`, `#kw-jo-…`, `#foodics-…`) get no pricing. The discount policy and the channel map are team-only: they live in the `POLICY_JSON` secret, never in the repo.
- Keep Salesforce line-item names exactly as they are in `reselling-copilot/data/catalog.json`.
- Run `npm run check` before proposing a change. Add a test when you touch `reselling-copilot/src/policy.ts` or `reselling-copilot/src/prompt.ts`.
- When reviewing PRs, flag any change that could leak one partner's pricing to another partner or expose discount rules in a partner channel.
- The reseller bot is `reselling-brain/` in this repo (Python, deployed on Railway from `main`). Follow the root `AGENTS.md` for it: `knowledge/` holds the common layer only (`audience: base` or `sales`); team, manager, cost and owner knowledge stays in the `BRAIN_OWNER_KNOWLEDGE_B64` secret. Run `cd reselling-brain/slack-bot && python -m unittest test_brain test_app`. Never propose changes to `orbit-reselling-wizard` (Orbit) as part of this work.
