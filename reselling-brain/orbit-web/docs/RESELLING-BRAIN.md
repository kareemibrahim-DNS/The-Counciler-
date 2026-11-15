# Reselling Brain in Orbit

Page: `/reselling-brain.html` · API: `/api/brain`

## Access (layers decided by Kareem, 14 Nov 2026)
| Who | Level | Sees |
| --- | --- | --- |
| Owner | owner | Everything, including pricing, markups, targets, strategy, partner contacts, trackers and contract status |
| Approved employee with a role (Partnerships team, managers) | team | Policy, churn rules, SLAs, processes, partner roster and the catalogue. **No** partner contacts, trackers or contract status |
| Sales / AMs (Slack bot) | sales | Only available resellers, list prices and each partner's commercial structure |
| Partner, revoked or unassigned | — | No access (403) |

The `sales-scope` knowledge file is shown to the sales level only. A doc with an unknown audience is owner-only.

## Switch it on
Set these in Cloudflare Pages → Settings → Variables (Production and Preview separately):
- `ANTHROPIC_API_KEY` (secret, required). Without it the API returns `brain_not_configured`.
- `BRAIN_MODEL` (optional, default `claude-sonnet-5-5`)
- `BRAIN_DAILY_LIMIT` (optional, default 200 questions per employee per day; the Owner is not limited)

## Privacy
Questions and answers are not stored. Each question writes one `audit_events` row (`brain_ask`) used for the daily limit.

## Updating the knowledge
The shared source lives in `reselling-brain/` (knowledge files, catalogue and the Slack bot).
`functions/_lib/reselling-brain-knowledge.js` and `functions/_lib/reselling-brain-catalog.js` are generated with
`node scripts/build-brain-knowledge.mjs`. Do not edit them by hand. The build fails if the catalogue ever contains a
cost, margin, markup, wholesale, payout or commission field.

## Orbit data tools (read-only)
The Brain can look up live Orbit data while answering. Each tool checks the caller's own module access on every call, so the Brain never shows more than the person could already open in Orbit.

| Tool | Needs | Returns |
| --- | --- | --- |
| `brain_catalog` | Any Brain user (Owner or approved employee) | Partner profile, quote rules, line items with Salesforce **list** prices by country, or a same-category comparison. Never cost or margin. |
| `orbit_partners` | Partners: view/edit | Partner names and status |
| `orbit_arr` | ARR: view/edit | ARR totals by category for a date range, optionally per partner or by month |
| `orbit_tickets` | Partners: view/edit | Slack ticket counts by partner, country and status |

All values are bound parameters. No tool writes. At most 5 tool turns per question.
