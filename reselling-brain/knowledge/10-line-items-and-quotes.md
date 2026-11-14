---
id: line-items-and-quotes
audience: team
source: Salesforce Standard Price Book + USD 1 – International (refreshed 14 Nov 2026); the old internal price-list sheet Policy tab (3 Oct 2026)
updated: 2026-11-14
---
# Line items, list prices and quote structure

## Where the numbers come from
- Every partner's line items and **list (selling) prices** are in the catalogue tool `brain_catalog`. Source: Salesforce Standard Price Book (SAR, AED, KWD, JOD, EGP) and "USD 1 – International", refreshed 14 Nov 2026. 29 partners, about 200 line items.
- Always call `brain_catalog` for a price. Never quote a price from memory, from another country, or from an old sheet.
- Use the **exact Salesforce line-item name** in every quote.
- A line with no price in a currency is **not sellable in that country**. Say so; do not convert currencies.
- Lines marked ⚠ have inconsistent prices across currencies: tell the person to verify in Salesforce before quoting.
- The catalogue holds list prices only. Cost, markup and margin are owner-only and are never in the catalogue.

## Country → currency
KSA → SAR · UAE → AED · Kuwait → KWD · Jordan → JOD · Egypt → EGP · anywhere else → USD (International price book).

## How to build a quote
1. Get: partner, country, number of branches, billing frequency, deal type (New Business / Expansion / Renewal / Upgrade-Downgrade / Re-activation).
2. Call `brain_catalog` with the partner and country. Follow that partner's quote rules exactly.
3. Show: Line item | Type | Qty | Unit list price | Line total, then the total, with the arithmetic.
4. Run the structure checks below.
5. Add discount eligibility (next section) and the Standard T&C block from 01-policy.

## Structure checks (most common mistakes)
- **Main + Additional:** most partners are 1 Main license + (branches − 1) Additional Branch lines of the same plan (BrandWallet, ShopBrain, FlowERP, Prepit, Ordable, Xero, QuickBooks, Alpha). License count must equal branch count.
- **Branches included in the plan:** Wafeq Premium = 1 branch only; Wafeq Enterprise includes 3 (Additional Branch only on Enterprise). Zyda Basic includes 1, Zyda Advanced includes 3.
- **Minimums:** Supy needs at least 3 licenses, plus a one-time Onboarding Fee on new business.
- **Per account, not per branch:** InvoiceQ and Iisal. InvoiceQ Basic covers up to 2 terminals; InvoiceQ Advanced is per issuing terminal. Iisal tier is chosen by yearly invoice volume.
- **Virtual brands:** Grubtech = Virtual Brand add-on per extra brand; Deliverect = Virtual License per virtual branch.
- **Usage lines:** OptCulture SMS and WhatsApp are billed per message on top of the license. Tell the merchant.
- **Only with SAP:** Malachite cannot be sold without SAP.
- **Inactive:** Nitx is deactivated. Never quote it.
- **One-time fees** (implementation, onboarding, customization) are never discounted.

## Discount eligibility (Kareem's discount policy, 3 Oct 2026)
- Allowed on **New Business only**. Expansion, Renewal, Upgrade/Downgrade, Re-activation: no discount. Retention (churn risk): Kareem decides.
- By branch count: 1–2 → no discount · 3–5 → minimum of the range · 6–7 → 50% of the maximum · 8–14 → 75% of the maximum · 15–21 → 100% of the maximum · 22+ → Kareem decides.
- Range by billing: Annual 4%–10% · Monthly, Quarterly, Semi-annual 3%–8% · One-time fees never.
- A merchant with a prior Marketplace discount is capped at the lowest band.
- Every approval is Kareem's. Escalation: Hatem Ashour. CC reseller@foodics.com. Response SLA: 2 KSA working days (Sun–Thu).
- Never put these bands in a message to a merchant or partner. Show the final price only.

## Telling partners in the same category apart
Call `brain_catalog` with a `category` to get a side-by-side (best for, edge, licensing unit, countries, entry price, watch-outs). Be precise about the differences and end with a one-line recommendation for the merchant described. Examples:
- Ordering platforms: Grubtech (multi-brand, kitchen + dispatch) · Deliverect (menu control and analytics, highest price) · UrbanPiper (lowest entry, only option for Egypt) · FeedUs (KSA local aggregators only).
- Inventory: ShopBrain (tiered per branch, mid price, optional accounting) · Supy (premium per outlet, 3-license minimum, deepest procurement and recipe costing).

## Known data issues (verify before quoting)
- The the old internal price-list sheet price list does not match Salesforce, and its KSA column holds KWD values for Ordable, Zyda and Mnasati. Salesforce wins.
- Eight VOLT lines have inconsistent prices across currencies (flagged ⚠).
- ShopBrain Essential has no main-branch line in Salesforce, only additional-branch lines.
