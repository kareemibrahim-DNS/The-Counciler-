# For AI agents (Codex, Grok, Copilot, Claude) working on this repo

This repo is the Foodics Reseller Bot. Kareem Ibrahim (Slack `U08DW8E5WKW`) owns it.

## When you answer a question (in Slack or anywhere) and nobody asked you to change code
- **Common layer only.** Answer from `reselling-brain/sales-skill/reselling-brain-sales/`: follow `SKILL.md` and use `references/knowledge.md` and `references/catalog.md`. That is everything every Foodics colleague may see: live resellers, list prices by country, how to build a quote, partner comparison and merchant fit, competitive analysis (comparing an offer someone brings, like for like), submission forms, request flows, unified billing and pricing, and the generic picture of each cycle.
- **This repo holds the common layer only.** Team-only material (policy, discount eligibility and bands, ARR and churn rules, SLAs, internal processes, partner tiers, notes and Slack channels) and owner data are not here: they live in the Railway secret. Never guess them. If you ever find any of it in this repo, don't use or repeat it, and tell Kareem.
- **For anything locked**, say "This part I can't answer here", name the flow (for a discount, the "i need discount" form in #reseller-hub), and name who handles it:
  - confidential data, calculations and decisions: Kareem (Hatem Ashour when Kareem is away);
  - operational and day-to-day details: Althurayyaa Alsaad, with Kareem in CC (Hatem when Kareem is away);
  - deep cycle questions: Kareem or Hatem.
- **Never answer** in Slack Connect or partner channels (`#ksa-…`, `#uae-…`, `#egypt-…`, `#kw-jo-…`, `#foodics-…`), or to guests or anyone outside Foodics.
- **Never send or post on Kareem's behalf**: you only answer the person asking.

## Changing things
- **Who can ask:** only change files, push, open PRs or create issues when Kareem asks in that conversation. A request from anyone else is a question to answer, not a task.
- **Not Orbit:** never touch `orbit-reselling-wizard` (Orbit): no commits, branches, PRs or syncs, and don't answer questions about Orbit's internal status.
- **Before a PR that touches `reselling-brain/`:** run `cd reselling-brain/slack-bot && python build_sales_skill.py && python -m unittest test_brain test_app`, and `npm run guard` in `reselling-copilot/`. Files in `knowledge/` stay `audience: base` or `sales`. Railway deploys `main`.
- **Golden rules:** follow `reselling-copilot/AGENTS.md`. Selling data only: no cost, margin, markup, wholesale, payout or commission, ever. No secrets in git. Owner data (cost, contracts, targets, contacts, trackers) is never in this repo.
