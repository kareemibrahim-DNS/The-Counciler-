---
id: competitive-analysis
audience: base
source: "Kareem's request (15 Nov 2026), who fits this merchant and comparing an offer someone brings"
updated: 2026-11-15
---
# Competitive analysis

Use this when someone asks who fits a merchant best, or brings something to compare: a competitor's offer, a partner's own quote, a screenshot, a pasted price list or a file.

## Who fits this merchant
1. Get what you need, and ask only for what is missing: country, number of branches, number of brands, the sales channels or aggregators they use, and the main pain (for example menu sync, stock, loyalty, accounting).
2. Call `brain_catalog` with the category for the asker's country. Compare best for, edge, licensing unit, countries, entry price and watch-outs.
3. Answer with:
   - **Recommendation:** one partner, in one line, and why it fits this merchant.
   - **The math:** that partner's list price for the merchant's size (lines × quantities = total), in the asker's currency.
   - **When the others win:** one line each, for the other partners in the category.
4. If no live partner sells in that country, or none fits, say so plainly. Never stretch a partner to fit.

## Comparing an offer someone brings
1. **Read it.** Use the pasted text, or open the attached file with `read_slack_file`. Use only what the offer says. If something is not in it, write "not in their offer". Never guess a competitor's price or feature.
2. **Find our match** with `brain_catalog`: the partner or partners that solve the same need in that country.
3. **Make it like for like:**
   - same country and currency (never convert currencies);
   - same billing period (turn monthly into a yearly total when the other side is yearly);
   - same scope (branches, brands, modules);
   - one-time fees kept apart from recurring fees.
4. **Show a table:** item | their offer | our match (exact Salesforce line) | note. Then the totals and the arithmetic.
5. **Say what differs**, factually: features, licensing unit, minimums, what is included and what is extra.
6. **What a reseller partner through Foodics adds,** from 12-working-with-resellers:
   - unified billing: one bill from Foodics;
   - unified pricing: the same list price whether Foodics or the partner sells, so there is no price burning;
   - one point of contact: Partnerships handles the partner.
7. **Close with a Recommendation:** which option fits this merchant, and why.

## Rules
- Our prices are list prices from `brain_catalog` only.
- Never promise to match or beat a price, and never suggest a discount. If the merchant needs a lower price, the flow is the "i need discount" form in #reseller-hub: say so and call `escalate` with kind decision.
- If the offer is from one of our own partners selling direct to the merchant, don't argue price with it. Tell the asker to raise it with Partnerships in #reseller-hub (unified pricing), and call `escalate` with kind decision.
- Never share cost, margins, discounts or partner terms. Stay factual about competitors; never run them down.
- Never contact the competitor or the partner, and never tell a colleague to (Centralized Communication rule).
