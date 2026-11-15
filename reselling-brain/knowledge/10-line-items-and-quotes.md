---
id: line-items-and-quotes
audience: base
source: Salesforce Standard Price Book + USD 1 – International (refreshed 14 Nov 2026)
updated: 2026-11-14
---
# Line items, list prices and quote structure

## Where the numbers come from
- Every partner's line items and **list (selling) prices** are in the catalogue tool `brain_catalog`. Source: Salesforce Standard Price Book (SAR, AED, KWD, JOD, EGP) and "USD 1 – International", refreshed 14 Nov 2026. 29 partners, about 200 line items.
- Always call `brain_catalog` for a price. Never quote a price from memory, from another country, or from an old sheet.
- Use the **exact Salesforce line-item name** in every quote.
- A line with no price in a currency is **not sellable in that country**. Say so; do not convert currencies.
- Lines marked ⚠ have inconsistent prices across currencies: tell the person to verify in Salesforce before quoting.
- The catalogue holds list prices only. Cost, markup and margin are locked and are never in the catalogue.

## Country → currency
KSA → SAR · UAE → AED · Kuwait → KWD · Jordan → JOD · Egypt → EGP · anywhere else → USD (International price book).

## One country per answer
- Show prices for **one country only**: the one named in the question; otherwise the asker's own country if you know it; otherwise ask "Which country is this for (KSA, UAE, Kuwait, Jordan, Egypt or International)?" before quoting.
- Never list every country's price unless the person asks for all countries or a comparison across countries.

## How to build a quote
1. Get: partner, country, number of branches, billing frequency, deal type (New Business / Expansion / Renewal / Upgrade-Downgrade / Re-activation).
2. Call `brain_catalog` with the partner and country. Follow that partner's quote rules exactly.
3. Show: Line item | Type | Qty | Unit list price | Line total, then the total, with the arithmetic.
4. Run the structure checks below.
5. If the merchant asks for a discount, don't promise or estimate one. Point to the discount flow in 12-working-with-resellers.

## Structure checks (most common mistakes)
- **Main + Additional:** most partners are 1 Main license + (branches − 1) Additional Branch lines of the same plan (BrandWallet, ShopBrain, FlowERP, Prepit, Ordable, Xero, QuickBooks, Alpha). License count must equal branch count.
- **Branches included in the plan:** Wafeq Premium = 1 branch only; Wafeq Enterprise includes 3 (Additional Branch only on Enterprise). Zyda Basic includes 1, Zyda Advanced includes 3.
- **Minimums:** Supy needs at least 3 licenses, plus a one-time Onboarding Fee on new business.
- **Per account, not per branch:** InvoiceQ and Iisal. InvoiceQ Basic covers up to 2 terminals; InvoiceQ Advanced is per issuing terminal. Iisal tier is chosen by yearly invoice volume.
- **Virtual brands:** Grubtech = Virtual Brand add-on per extra brand; Deliverect = Virtual License per virtual branch.
- **Usage lines:** OptCulture SMS and WhatsApp are billed per message on top of the license. Tell the merchant.
- **Only with SAP:** Malachite cannot be sold without SAP.
- **Inactive:** Nitx is deactivated. Never quote it.

## Telling partners in the same category apart (and who fits this merchant)
Call `brain_catalog` with a `category` to get a side-by-side (best for, edge, licensing unit, countries, entry price, watch-outs, how to choose). Be precise about the differences. When someone describes a merchant or a business case, recommend the partner that fits it best and say why, in one line, labelled "Recommendation". Examples:
- Ordering platforms: Grubtech (multi-brand, kitchen + dispatch) · Deliverect (menu control and analytics, highest price) · UrbanPiper (lowest entry, only option for Egypt) · FeedUs (KSA local aggregators only).
- Inventory: ShopBrain (tiered per branch, mid price, optional accounting) · Supy (premium per outlet, 3-license minimum, deepest procurement and recipe costing).

## Known data issues (verify before quoting)
- Older internal price lists don't match Salesforce. Always use `brain_catalog`: Salesforce wins.
- Eight VOLT lines have inconsistent prices across currencies (flagged ⚠).
- ShopBrain Essential: its main-branch lines are inactive in Salesforce (since June 2026); only the Additional Branch lines are active, so an Essential quote can't be built correctly yet. Check in #reseller-hub.
