# Reports

Point-in-time checks made while building the reseller bot. List (selling) prices only; no cost, margin or markup.

## Data issues to fix at the source (15 Nov 2026)
Salesforce is the source the bot quotes from, so these show up in answers until someone fixes them in Salesforce.
- **ShopBrain Essential:** its main-branch lines exist but are **inactive** (since June 2026); only the Additional Branch lines are active. An Essential quote can't be built correctly.
- **VOLT:** eight lines have prices that don't match across currencies (flagged ⚠ in the catalogue). For example, Hosting with SAP [Monthly] is USD 5,000 but SAR 1,750, and Attendance License [Monthly] is SAR 2 but AED 204.04.
- **wi-Q Connect:** AED, KWD, JOD and EGP list prices rose 15–40% after the 5 Nov export; the catalogue was refreshed on 14 Nov (`reselling-copilot/scripts/refresh-prices.mjs`).

## The old internal price-list sheet vs Salesforce (14 Nov 2026)
`internal-price-list-vs-salesforce-2026-11-14.csv`, one row per line and currency:
- **Price differs:** 231 prices don't match Salesforce.
- **Wrong currency:** 12 lines hold KWD values in the KSA (SAR) column (Ordable, Zyda, Mnasati, UrbanPiper 1 Channel).
- **Iisal tiers:** the sheet looks inverted (Up to 500 = 6,282 vs Salesforce 2,725; 500+ = 1,320 vs 6,800).
- **Lines not in Salesforce:** 127 sheet lines, mostly billing options Salesforce doesn't sell, such as Semi-Annual and Quarterly.
- **Lines missing from the sheet:** 101 Salesforce lines.

Recommendation: mark the tab "outdated – use Salesforce" so nobody quotes from it. The bot always quotes Salesforce.

## Security reviews of the Slack bot (14–15 Nov 2026)
Three independent reviews tried to make the bot show someone more than their layer allows. Every confirmed finding was fixed and covered by tests (`slack-bot/test_brain.py`, `slack-bot/test_app.py`).
1. **Leak audit:** 23 confirmed. Who reads the reply now decides the level. Partners, guests and Slack Connect users get nothing. Owner answers happen only in Kareem's DM. Links are filtered and previews are off.
2. **Fix review:** 13 confirmed. Public channels get the sales level. The link filter was rewritten. Kareem sees the exact fact a `learn` call queues, and cost or markup facts can't reach the team.
3. **Layers review:** 31 confirmed. Thread mentions now read the thread. The `away`/`back` state survives deploys. Tools have hard floors. Hand-offs never mention anyone twice and never appear under an error.
