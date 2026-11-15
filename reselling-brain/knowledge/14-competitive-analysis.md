---
id: competitive-analysis
audience: base
source: "Kareem's request (15 Nov 2026), who fits this merchant, comparing two of our partners and comparing an offer someone brings"
updated: 2026-11-15
---
# Competitive analysis

Use this when someone asks who fits a merchant best, how two of our partners compare, or brings something to compare: a competitor's offer, a partner's own quote, a screenshot, a pasted price list or a file.

## Which country
- Use the **merchant's** country when the question says where the merchant is (a city counts: Riyadh → KSA, Dubai → UAE, Kuwait City → Kuwait, Amman → Jordan, Cairo → Egypt). Otherwise use the asker's country. If it isn't clear, ask.
- Outside the five markets (for example Bahrain, Qatar, Oman): use the USD (International) prices only.
- A line with no price in that currency is not sold there. If a partner lists the country but has no price there, say so and don't recommend it there until Partnerships confirms in #reseller-hub.

## Who fits this merchant
1. Get what you need, and ask only for what is missing: country, number of branches, number of brands, the sales channels or aggregators they use, and the main pain (for example menu sync, stock, loyalty, accounting).
2. Call `brain_catalog` with the category for that country. Pick on the category's "How to choose" first, then compare best for, edge, licensing unit, countries, price and watch-outs.
3. Answer with:
   - **Recommendation:** one partner, in one line, and why it fits this merchant.
   - **The math:** that partner's full quote for the merchant's size (lines × quantities = total), not just the entry price.
   - **When the others win:** one line each, for the other partners in the category.
4. Several needs (for example ordering and loyalty): one Recommendation per need, each from its own category. Two partners that fit equally: say it's close and name the one question that decides it.
5. If no live partner sells in that country, or none fits, say so plainly. Never stretch a partner to fit.

## Comparing two of our partners
Use this when someone asks how one of our partners compares with another (for example "Grubtech or Deliverect?", "Xero vs Wafeq for this merchant").
1. Call `brain_catalog` with `compare` (the partner names) and the merchant's country. If a name isn't one of our partners, it's a competitor: follow "Comparing an offer someone brings".
2. **Same category:** show a table: | | partner A | partner B | with best for, edge, licensing unit, billing, countries, entry price (exact Salesforce line name) and watch-outs. Then use the category's "How to choose" to say which one fits. With the merchant's size, add the math for both: full quote totals, same billing period, recurring fees apart from one-time fees.
3. **Different categories:** say they solve different needs and aren't alternatives, and name what each one is for. If the merchant needs both, give one Recommendation per need.
4. A partner with no price in that country isn't sold there: say so and don't recommend it there.
5. Close with a **Recommendation** and the one question that decides it if it's close. Never say one partner is bad; say when each one wins.

## Comparing an offer someone brings
1. **Read it.** Use the pasted text, or open the attached file with `read_slack_file`. Use only what the offer says. If something is not in it, write "not in their offer". Never guess a competitor's price, feature or billing frequency. If a screenshot or file is unclear or cut off, list what you could read and ask for the rest. If their offer has no prices, compare scope and features only.
2. **Only a competitor's name, no offer:** the Reselling Brain holds no competitor data. Don't describe their product or prices from memory. Ask for their offer, and meanwhile give our side: the partner that fits and its price for the merchant's size.
3. **Find our match** with `brain_catalog`: the partner or partners that solve the same need in that country.
4. **Make it like for like:**
   - **Same billing period.** Use our line for the same period when the partner has one (monthly against monthly, annual against yearly). If our partner is sold only annually, turn their monthly price into a full-year total and say ours is billed annually.
   - **Same scope:** branches, brands, modules. If the catalogue doesn't say whether one line covers all branches, say so and ask to confirm in #reseller-hub before treating the prices as equal.
   - **Different licensing units** (per user, per device or per order against our per branch or per account): compare totals for the merchant's real size, never unit price against unit price.
   - **One-time fees stay apart** from recurring fees, on both sides. The headline and the Recommendation compare recurring fees only. A first-year total that adds the one-time fees can be an extra line, never the headline.
   - **Same currency only.** If their offer is in another currency, show both sides in their own currency, side by side. Never convert either side and don't say which is cheaper.
   - If their offer shows a price cut or free months, compare what the merchant pays over a full year using only what the offer states.
5. **Show a table:** item | their offer | our match (exact Salesforce line name) | note. Then the totals and the arithmetic.
6. **Say what differs**, factually, without guessing what a partner covers when the catalogue doesn't say (for example which aggregators); mark it to confirm in #reseller-hub: features, licensing unit, minimums, what is included and what is extra. Something in their offer we don't match: write "no match in our catalogue". A feature the catalogue doesn't mention: write "not in the Reselling Brain", not "our partner doesn't have it".
7. **What a reseller partner through Foodics adds,** from 12-working-with-resellers:
   - unified billing: one bill from Foodics;
   - unified pricing: the list price is the same whether Foodics or the partner sells it, so there is no price burning;
   - one point of contact: Partnerships handles the partner.
8. **Close with a Recommendation** (which option fits this merchant, and why) and the next step: build the quote, then submit it with that partner's form.

## When the asker wants something to send the merchant
- Write a draft only; the asker sends it.
- Keep the comparison table, the totals, what's included, and what buying through Foodics adds.
- Leave out watch-outs, "When the others win", partners you didn't recommend, Partnerships' internal flows and channels, and the words "price burning".

## Rules
- Our prices are list prices from `brain_catalog` only. Keep exact Salesforce line names, even in an Arabic reply.
- You may show the difference between two totals in the same currency. Don't turn it into a price to beat.
- Never promise to match or beat a price, and never suggest a discount. Bring up the discount flow only when the asker asks for a lower price or a match: then it's the "i need discount" form in #reseller-hub, say so and call `escalate` with kind decision.
- If the offer is from one of our own partners selling direct to the merchant, don't argue price with it. Tell the asker to raise it with Partnerships in #reseller-hub (unified pricing), and call `escalate` with kind decision.
- An offer from a company we don't resell can't be quoted, billed or submitted through us. If the asker wants Foodics to resell it, that's new partner outreach: call `escalate` with kind decision.
- Never share cost, margins, discounts or partner terms. Stay factual about competitors; never run them down.
- Never contact the competitor or the partner, and never tell a colleague to (Centralized Communication rule).
