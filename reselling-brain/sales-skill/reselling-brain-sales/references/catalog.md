# Reseller catalogue: available resellers, list prices, quote structure

Source: Salesforce Standard Price Book + "USD 1 – International", refreshed 14 Nov 2026. LIST (selling) prices only.
A blank price means the line is not sold in that country. Never convert between currencies.

## Categories
- **Ordering platform management**: Grubtech, Deliverect, UrbanPiper, FeedUs
- **Loyalty & CRM**: BrandWallet, Koinz, OptCulture, Prepit
- **Online ordering & web store**: Ordable, Zyda, Mnasati, wi-Q
- **Inventory**: ShopBrain, Supy
- **Accounting**: Wafeq, Xero, Alpha (Xero), QuickBooks
- **ERP**: FlowERP, SAP, MS Dynamics
- **E-invoicing & digital receipts**: InvoiceQ, Iisal
- **HR & payroll**: VOLT, Malachite
- **Table management**: Servme
- **Other**: Ishbek, Roboost, Nitx

# Category: Ordering platform management

How to choose: Pick on which aggregators the merchant uses, single vs multi-brand, and country.

## Grubtech
- Category: Ordering platform management
- What it is: Connects online ordering channels to Foodics POS and adds kitchen management and delivery dispatch in one platform. 300+ integrations.
- Best for: Multi-brand operators and cloud kitchens that want order flow, kitchen tracking and dispatch together.
- Edge: Live order tracking from prep to dispatch; multi-brand, multi-location from one setup; widest integration list.
- Licensing unit: gOnline License per branch (main line). Virtual Brand add-on for each extra brand on the same branch.
- Countries: KSA, UAE, Kuwait, Jordan
- Watch out: Menu sync is the most common support issue. Confirm menu setup ownership before go-live.
- Submit deals with: https://share.hsforms.com/1rOFHTm1gTpepWC29FiQGzQ5c1ve (KSA approval form: No (Partnerships handles KSA))
- Quote structure:
  - 1 gOnline License per physical branch.
  - Each additional brand on a branch = 1 Virtual Brand line.
  - Sold Monthly or Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Grubtech - Virtual Brand [Annual] | Add-on | Annual | 710.5 | 970.9 | 82 | 101.5 | 7,150 | 268.2 |
| Grubtech - Virtual Brand [Monthly] | Add-on | Monthly | 64.6 | 88.3 | 7.5 | 9.2 | 650 | 24.5 |
| Grubtech - gOnline License [Annual] | Main | Annual | 1,421.1 | 1,942 | 164 | 203 | 14,300 | 536.3 |
| Grubtech - gOnline License [Monthly] | Main | Monthly | 129.2 | 176.5 | 14.911 | 18.46 | 1,300 | 48.8 |

## Deliverect
- Category: Ordering platform management
- What it is: Connects online ordering channels to Foodics POS so orders and menus are managed in one place, with sales and third-party delivery analytics.
- Best for: Brands that care most about central menu control and channel analytics.
- Edge: Strongest menu management with location-specific variations; real-time sales analytics across channels.
- Licensing unit: Physical License per physical branch; Virtual License per virtual branch.
- Countries: KSA, UAE, Kuwait, Jordan
- Watch out: Highest price in the category. Annual only in Salesforce.
- Submit deals with: https://welcome.deliverect.com/foodics-bundle (KSA approval form: No (Partnerships handles KSA))
- Quote structure:
  - 1 Physical License per physical branch (includes 1 physical branch).
  - 1 Virtual License per virtual branch (includes 1 virtual branch).
  - Annual billing in Salesforce.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Deliverect - Physical License - [Annual] | Main | Annual | 3,150 | 3,438.79 | 290.47 | 665.27 | 46,850 | 937 |
| Deliverect - Virtual License - [Annual] | Add-on | Annual | 1,688 | 2,113.92 | 178.56 | 408.96 | 28,800 | 576 |

## UrbanPiper
- Category: Ordering platform management
- What it is: Connects online ordering channels to Foodics POS; control menus, stock availability and business data across platforms and outlets.
- Best for: Price-sensitive merchants, and the only aggregator-management option for Egypt.
- Edge: Lowest entry price in KSA; real-time stock availability across outlets.
- Licensing unit: Subscription License per outlet. '1 Channel' license for merchants on a single aggregator.
- Countries: KSA, UAE, Egypt
- Watch out: The 1 Channel line has no SAR price. It can't be quoted in KSA.
- Submit deals with: https://tally.so/r/Xx11k4 (KSA approval form: No (Partnerships handles KSA))
- Quote structure:
  - 1 Subscription License per outlet.
  - 1 Channel variant is limited to one channel and has no KSA price.
  - Monthly or Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Urban Piper - Subscription License [Annual] | Main | Annual | 1,170 | 1,822.28 | 167.895 | 222.3 | 15,022.8 | 588 |
| Urban Piper - Subscription License [Monthly] | Main | Monthly | 128.34 | 184.23 | 16.974 | 24.385 | 1,647.89 | 55.89 |
| UrbanPiper - 1 Channel [Annual] | Add-on | Annual |  | 1,541.4 | 130.2 | 204.48 | 14,650.56 | 420 |
| UrbanPiper - 1 Channel [Monthly] | Add-on | Monthly |  | 143.13 | 12.09 | 19.53 | 1,398.93 | 39 |

## FeedUs
- Category: Ordering platform management
- What it is: Connects HungerStation, Jahez, Mrsool and other online channels to Foodics POS; unified menu control and branch-specific provider mapping.
- Best for: KSA merchants whose orders come from local Saudi aggregators.
- Edge: Local-aggregator focus and branch-level provider assignments.
- Licensing unit: Subscription License per branch.
- Countries: KSA only
- Watch out: SAR only. Not sellable outside KSA.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLSeHp1QSysXGWgxilSlD3mSiEgDexgPFQFAG4yUVDpGPZNI-tQ/viewform (KSA approval form: No (Partnerships handles KSA))
- Quote structure:
  - 1 Subscription License per branch.
  - Annual, SAR only.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| FeedUs - Subscription License [Annual] | Main | Annual | 2,300 |  |  |  |  |  |

# Category: Loyalty & CRM

How to choose: Pick on how deep the merchant goes: quick wallet cards, loyalty plus feedback and ordering, or a full CRM with campaigns.

## BrandWallet
- Category: Loyalty & CRM
- What it is: Digital loyalty cards (stamp, multi-stamp, point, tiered) with automated rewards, coupons, location push alerts and QR table tents.
- Best for: Cafés and QSRs that want wallet loyalty cards live fast, in any country.
- Edge: Plans are tiered by number of cards: Basic 1, Standard 2, Growth 5.
- Licensing unit: One plan for the main branch plus one Additional Branch line per extra branch.
- Countries: Global
- Watch out: License count must equal branch count. 6 branches = 1 plan + 5 Additional Branch.
- Submit deals with: https://foodics-sales.brand-wallet.com/PZQ5AqGEWaO7LyY9 (KSA approval form: Yes)
- Quote structure:
  - 1 Main plan (Basic / Standard / Growth) + (branches − 1) Additional Branch.
  - Additional Branch works with all plans.
  - Monthly or Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| BrandWallet - Additional Branch [Annual] | Additional | Annual | 900.01 | 882 | 73.573 | 171 | 11,280.15 | 240 |
| BrandWallet - Additional Branch [Monthly] | Additional | Monthly | 75 | 73.45 | 6.131 | 14.2 | 940 | 20 |
| BrandWallet - Basic Plan [Annual] | Main | Annual | 2,154.9 | 2,107.9 | 175.9 | 406.9 | 23,400 | 573.8 |
| BrandWallet - Basic Plan [Monthly] | Main | Monthly | 219.9 | 214.9 | 17.9 | 41.49 | 2,280 | 58.5 |
| BrandWallet - Growth Plan [Annual] | Main | Annual | 2,928.9 | 2,864.9 | 240 | 553 | 31,800 | 780 |
| BrandWallet - Growth Plan [Monthly] | Main | Monthly | 317 | 310 | 26 | 59.9 | 3,300 | 84.5 |
| BrandWallet - Standard Plan [Annual] | Main | Annual | 2,872 | 2,809.9 | 235 | 542.5 | 29,400 | 765 |
| BrandWallet - Standard Plan [Monthly] | Main | Monthly | 292.9 | 286.49 | 24 | 54.9 | 2,880 | 78 |

## Koinz
- Category: Loyalty & CRM
- What it is: Loyalty plus customer feedback, growth analytics, retargeting, and online ordering for pickup and delivery.
- Best for: KSA or Egypt merchants who want loyalty, feedback and their own ordering in one package.
- Edge: WhatsApp messaging in KSA, SMS in Egypt; Apple Wallet; built-in ordering.
- Licensing unit: Single Loyalty Package.
- Countries: KSA, Egypt, UAE (no AED price)
- Watch out: Priced in SAR and EGP only.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLScSNaZ0Ih5peHu2NBRMS0U1MYnLS7CcxereCUEqdzL-xI260g/viewform (KSA approval form: Yes)
- Quote structure:
  - One Loyalty Package line.
  - WhatsApp is KSA only; SMS is Egypt only.
  - Monthly or Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Koinz - Loyalty Package - [Annual] | Main | Annual | 1,800 |  |  |  | 14,400 |  |
| Koinz - Loyalty Package - [Monthly] | Main | Monthly | 300 |  |  |  | 1,200 |  |

## OptCulture
- Category: Loyalty & CRM
- What it is: AI-powered loyalty and CRM: interactive digital receipts, personalized loyalty, automated campaigns, Apple and Google Wallet cards, Customer 360.
- Best for: Mid-to-large brands that want a CRM with segmentation and automated campaigns, not just a stamp card.
- Edge: Growth adds pre-built WhatsApp, SMS and email promotional campaigns on top of Loyalty.
- Licensing unit: Loyalty or Growth license, plus messaging billed per usage.
- Countries: KSA, UAE (also US, India)
- Watch out: SMS and WhatsApp are charged per message on top of the license. Tell the merchant up front.
- Submit deals with: Not provided (KSA approval form: Yes)
- Quote structure:
  - Choose Loyalty or Growth (Growth includes all Loyalty features).
  - Add SMS Usage and/or WhatsApp Usage lines (per message, GCC).
  - Monthly or Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| OptCulture - Growth - [Annual] | Main | Annual | 4,860 | 4,756 | 402 | 920 | 64,800 | 1,296 |
| OptCulture - Growth - [Monthly] | Main | Monthly | 405 | 396 | 33 | 77 | 5,400 | 108 |
| OptCulture - Loyalty - [Annual] | Main | Annual | 2,925 | 2,863 | 242 | 553.8 | 39,000 | 780 |
| OptCulture - Loyalty - [Monthly] | Main | Monthly | 244 | 239 | 20 | 46.15 | 3,250 | 65 |
| OptCulture - SMS Usage - GCC | Usage | Usage | 0.1 | 0.1 | 0.01 | 0.02 | 1.36 | 0.03 |
| OptCulture - WhatsApp usage - GCC | Usage | Usage | 0.25 | 0.25 | 0.02 | 0.05 | 3.4 | 0.07 |

## Prepit
- Category: Loyalty & CRM
- What it is: Behavior-based loyalty rewards, automated promotions and SMS, plus online ordering, payments and a waiter app.
- Best for: Egyptian merchants who want loyalty and ordering together.
- Edge: Advanced adds loyalty points, commercial account management and instant rewards.
- Licensing unit: Basic or Advanced license for the main branch + Additional Branch lines; Delivery Module and Mobile App add-ons.
- Countries: Egypt (also KSA, Canada)
- Watch out: EGP only in Salesforce. Advanced and Mobile App are high-value lines.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLSf8GJb_U_N2UMV6EYvssgza4JfQRB_kCd4wiPhkjaTnc6V7vA/viewform (KSA approval form: Yes)
- Quote structure:
  - 1 Main license (Basic or Advanced) + (branches − 1) matching Additional Branch.
  - Additional Branch must match the main tier.
  - Annual, EGP only.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Prepit - Advanced License (Additional Branch) [Annual] | Additional | Annual |  |  |  |  | 2,456 |  |
| Prepit - Advanced license [Annual] | Main | Annual |  |  |  |  | 50,088 |  |
| Prepit - Basic License (Additional Branch) [Annual] | Additional | Annual |  |  |  |  | 1,255 |  |
| Prepit - Basic License [Annual] | Main | Annual |  |  |  |  | 6,539 |  |
| Prepit - Delivery Management Module [Annual] | Add-on | Annual |  |  |  |  | 6,097 |  |
| Prepit - Mobile Application [Annual] | Add-on | Annual |  |  |  |  | 66,053 |  |

# Category: Online ordering & web store

How to choose: Pick on country first. Prices exist only in some currencies, so check that before anything else.

## Ordable
- Category: Online ordering & web store
- What it is: 0% commission online store connected to Foodics POS, with 60+ features, delivery, payment gateways and social marketing tools.
- Best for: Kuwait merchants who want their own branded ordering store.
- Edge: 0% commission; deep feature set; strong in Kuwait.
- Licensing unit: Basic or Advance license + Additional Branch; Mobile Application add-on.
- Countries: Kuwait, Bahrain, Qatar (Jordan priced)
- Watch out: Priced in KWD and JOD only. No KSA or UAE price.
- Submit deals with: Not provided (KSA approval form: Yes)
- Quote structure:
  - 1 Main license (Basic / Advance) + (branches − 1) Additional Branch.
  - Mobile Application is an optional add-on.
  - Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Ordable - Additional Branch [Annual] | Additional | Annual |  |  | 20 | 44 |  |  |
| Ordable - Advance License [Annual] | Main | Annual |  |  | 410 | 947 |  |  |
| Ordable - Basic License [Annual] | Main | Annual |  |  | 275 | 635 |  |  |
| Ordable - Mobile Application [Annual] | Add-on | Annual |  |  | 250 | 473 |  |  |

## Zyda
- Category: Online ordering & web store
- What it is: Direct ordering website set up in 24 hours at 0% commission, with one dashboard for orders, stock, delivery and marketing.
- Best for: Merchants in UAE, Kuwait or Egypt who want a fast, low-effort web store.
- Edge: Advanced already covers 3 branches, which is cheaper than stacking branches on Basic.
- Licensing unit: Basic includes 1 branch; Advanced includes 3 branches; Additional Branch for each extra; Mobile Application add-on.
- Countries: Global (priced KWD, AED, EGP)
- Watch out: No SAR or JOD price. Can't be quoted in KSA or Jordan.
- Submit deals with: https://mex87gdp4z7.typeform.com/to/S5JhEa0v (KSA approval form: Yes)
- Quote structure:
  - Basic = 1 branch; Advanced = 3 branches included.
  - Extra branches beyond what's included = Additional Branch lines.
  - Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Zyda - Additional Branch [Annual] | Additional | Annual |  | 1,728 | 144 |  | 15,000 |  |
| Zyda - Advanced Package [Annual] | Main | Annual |  | 5,040 | 420 |  | 52,500 |  |
| Zyda - Basic Package [Annual] | Main | Annual |  | 2,940 | 218 |  | 17,500 |  |
| Zyda - Mobile Application [Annual] | Add-on | Annual |  | 7,200 | 600 |  | 75,000 |  |

## Mnasati
- Category: Online ordering & web store
- What it is: Own online store live in about 24 hours; syncs menu, branches, customers and orders with Foodics.
- Best for: Kuwait merchants who need a store fast and know their catalog size.
- Edge: Tiered by catalog size: Premium allows 50 main and 150 sub categories, 1,500 products and bulk upload.
- Licensing unit: Basic or Premium package.
- Countries: Kuwait, Qatar, KSA (priced KWD, AED)
- Watch out: No SAR price in Salesforce, even though KSA is listed as a working country.
- Submit deals with: https://docs.google.com/forms/d/13UZOcC_pX0Ic14QMSvILejgq0gMpPFsrCE7l9VDmj5U/viewform (KSA approval form: Yes)
- Quote structure:
  - One package line (Basic or Premium) chosen by catalog size.
  - Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Mnasati - Basic Package [Annual] | Main | Annual |  | 3,500 | 250 |  |  |  |
| Mnasati - Premium Package - [Annual] | Main | Annual |  | 4,500 | 350 |  |  |  |

## wi-Q
- Category: Online ordering & web store
- What it is: Modular ordering: Connect, Online Ordering and Table (QR) Ordering.
- Best for: Dine-in venues that want QR table ordering, or a modular online ordering setup.
- Edge: The only partner here with QR table ordering, and the only one with Monthly, Quarterly, Semi-annual and Annual options.
- Licensing unit: Module licenses: Connect, Online Ordering, Table Ordering.
- Countries: Priced in all six currencies
- Watch out: Table Ordering is the highest-priced module. Quote modules separately.
- Submit deals with: Not provided (KSA approval form: No (Partnerships handles KSA))
- Quote structure:
  - Quote each module as its own line.
  - Connect is available Monthly, Quarterly, Semi-annual and Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| wi-Q - Connect - [Annual] | Main | Annual | 2,000 | 1,715 | 147 | 281.93 | 21,420 | 342 |
| wi-Q - Connect - [Monthly] | Main | Monthly | 170 | 145.06 | 12.555 | 24.139 | 1,829.96 | 29 |
| wi-Q - Connect - [Quarterly] | Main | Quarterly | 509 | 432.44 | 37.416 | 71.89 | 5,453.27 | 87 |
| wi-Q - Connect - [Semi-Annual] | Main | Semi-annual | 1,012 | 859.37 | 74.368 | 142.722 | 10,833.33 | 173 |
| wi-Q - Online Ordering - [Annual] | Main | Annual | 5,400 | 5,285 | 446 | 1,022 | 72,000 | 1,440 |
| wi-Q - Online Ordering - [Monthly] | Main | Monthly | 488 | 477 | 40 | 92 | 6,500 | 130 |
| wi-Q - Table Ordering - [Monthly] | Main | Monthly | 683 | 668 | 56 | 129 | 9,100 | 182 |
| wi-Q - Table Ordering- [Annual] | Main | Annual | 7,560 | 7,399 | 625 | 1,431 | 100,800 | 2,016 |

# Category: Inventory

How to choose: Pick on budget and depth: ShopBrain is tiered per branch, Supy is premium per outlet with a 3-license minimum.

## ShopBrain
- Category: Inventory
- What it is: Real-time inventory with AI demand planning, a restaurant accounting module and F&B expert insights.
- Best for: Single and multi-branch restaurants that want solid inventory at a mid price, with optional accounting.
- Edge: Operation adds the full PR/PO cycle; Enterprise adds advanced adjustments and COGS. The accounting add-on runs on the same POS data.
- Licensing unit: Tier per branch: Essential, Operation or Enterprise. Main license + Additional Branch. Accounting add-on (main + additional). Cost Center per warehouse or central kitchen.
- Countries: KSA, UAE, Egypt, Qatar
- Watch out: Essential has only Additional Branch lines in Salesforce, so the Essential main license is missing. Confirm before quoting Essential.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLSeSgfMm0SOBlcvU56fhSTOWEJK4YQSQE6WsNnHaRUwmx5ceTg/viewform (KSA approval form: Yes)
- Quote structure:
  - 1 Main (tier) + (branches − 1) Additional Branch of the same tier.
  - Accounting: 1 Accounting Main + (branches − 1) Accounting Additional Branch.
  - Each warehouse or central kitchen = 1 Cost Center.
  - Annual, Quarterly, or Monthly for additional lines.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| ShopBrain - Accounting Additional Branch [Annual] | Additional | Annual | 226 | 221 | 19 | 43 | 2,400 | 60 |
| ShopBrain - Accounting Additional Branch [Quarterly] | Additional | Quarterly | 59 | 58 | 5 | 11 | 630 | 16 |
| ShopBrain - Accounting Main [Annual] | Add-on | Annual | 1,576 | 1,542 | 131 | 299 | 10,800 | 420 |
| ShopBrain - Accounting Main [Quarterly] | Add-on | Quarterly | 414 | 405 | 34 | 78 | 2,835 | 110 |
| ShopBrain - Cost Center [Annual] | Add-on | Annual | 1,126 | 1,102 | 94 | 214 | 9,600 | 300 |
| ShopBrain - Cost Center [Quarterly] | Add-on | Quarterly | 295 | 289 | 25 | 56 | 2,520 | 79 |
| ShopBrain - Enterprise Plan - Additional Branch - [Annual] | Additional | Annual | 1,800 | 1,762.74 | 148.32 | 340.02 | 24,264 | 480 |
| ShopBrain - Enterprise Plan - [Annual] | Main | Annual | 4,500 | 4,404 | 372 | 852 | 21,000 | 1,200 |
| ShopBrain - Enterprise Plan- Additional Branch - [Monthly] | Additional | Monthly | 178.75 | 175.05 | 14.73 | 33.77 | 2,409.55 | 47.67 |
| ShopBrain - Enterprise Plan- [Quarterly] | Main | Quarterly | 1,181 | 1,156 | 98 | 224 | 5,513 | 315 |
| ShopBrain - Essential Plan - Additional Branch - [Monthly] | Additional | Monthly | 97.5 | 95.48 | 8.03 | 18.42 | 1,314.3 | 26 |
| ShopBrain - Essential Plan- Additional Branch - [Annual] | Additional | Annual | 900 | 881.37 | 74.16 | 170.01 | 12,132 | 240 |
| ShopBrain - Operation Plan - Additional Branch - [Annual] | Additional | Annual | 1,260 | 1,233.92 | 103.82 | 238.01 | 16,984.8 | 336 |
| ShopBrain - Operation Plan - [Quarterly] | Main | Quarterly | 827 | 809 | 68 | 157 | 5,040 | 221 |
| ShopBrain - Operation Plan- Additional Branch - [Monthly] | Additional | Monthly | 130 | 127.31 | 10.71 | 24.56 | 1,752.4 | 34.67 |
| ShopBrain - Operation Plan- [Annual] | Main | Annual | 3,150 | 3,083 | 260 | 596 | 19,200 | 840 |

## Supy
- Category: Inventory
- What it is: Inventory, smart procurement, invoices and supplier settlements, recipe and menu engineering, and BI on Foodics sales data.
- Best for: Groups with central kitchens that want procurement, recipe costing and supplier control.
- Edge: Deepest procurement and recipe-costing features in the category.
- Licensing unit: Regular Outlet License per outlet; Central Kitchen License per central kitchen; Extra Cost Center; one-time Onboarding Fee.
- Countries: KSA, UAE (also UK, Australia)
- Watch out: Minimum 3 licenses. About 2× ShopBrain Operation per outlet.
- Submit deals with: https://share.hsforms.com/1zJtdrnCcQOmv9G6xplalig5lyyw (KSA approval form: Yes)
- Quote structure:
  - Minimum 3 licenses in total.
  - 1 Regular Outlet per outlet; 1 Central Kitchen per central kitchen.
  - Add the one-time Onboarding Fee on new business.
  - Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Supy - Central Kitchen License [Annual] | Main | Annual | 7,020 | 6,870 | 580 | 1,329 | 93,600 | 1,872 |
| Supy - Extra Cost Center [Annual] | Add-on | Annual | 540 | 528 | 45 | 102 | 7,200 | 144 |
| Supy - Onboarding Fee [One-Time] | One-time | One-time | 1,875 | 1,835 | 155 | 355 | 25,000 | 500 |
| Supy - Regular Outlet License [Annual] | Main | Annual | 5,940 | 5,813 | 491 | 1,125 | 79,200 | 1,584 |

# Category: Accounting

How to choose: Pick on branch count and whether the merchant needs setup help.

## Wafeq
- Category: Accounting
- What it is: Cloud accounting that syncs Foodics sales; VAT returns, invoicing and payroll.
- Best for: Saudi and UAE merchants who want local, VAT-ready accounting.
- Edge: Local Arabic-first product; Enterprise covers 3 branches in one license.
- Licensing unit: Premium (1 branch only) or Enterprise (includes 3 branches) + Additional Branch on Enterprise only.
- Countries: KSA, UAE
- Watch out: Premium can't take extra branches. With 2+ branches, quote Enterprise.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLScDy932sEjgQ4M3BgGzsHnZ7A_O7tQDXoaS6L0e4Kd8DzDCCA/viewform (KSA approval form: Yes)
- Quote structure:
  - 1 branch → Premium.
  - 2–3 branches → Enterprise.
  - 4+ branches → Enterprise + (branches − 3) Additional Branch.
  - Annual.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Wafeq - Additional Branch -  Enterprise [Annual] | Additional | Annual | 540 | 540 | 45.45 | 104.25 | 3,981 | 147.14 |
| Wafeq - Enterprise Plan [Annual] | Main | Annual | 3,360 | 3,360 | 282.83 | 648.65 | 38,217.6 | 915.53 |
| Wafeq - Premium Plan [Annual] | Main | Annual | 2,340 | 2,340 | 196.97 | 451.74 | 24,151.4 | 637.6 |

## Xero
- Category: Accounting
- What it is: Xero subscription sold directly, with an optional Hesab Arabic interface and separate training and support packages.
- Best for: Merchants who already know Xero or need international accounting.
- Edge: Global brand; Arabic interface available as an add-on.
- Licensing unit: Main Subscription + Additional Branch; Hesab Arabic Interface add-on; Training and Support packages (one-time).
- Countries: All markets
- Watch out: Training and support are NOT included. Quote them separately if the merchant needs help.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - 1 Main Subscription + (branches − 1) Additional Branch.
  - Training and Support are separate one-time lines.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Xero - "Hesab" Arabic Interface [Annual] | Add-on | Annual | 1,950 | 1,735.5 | 159.9 | 370.5 | 25,038 | 527 |
| Xero - Additional Branch [Annual] | Additional | Annual | 780 | 694.2 | 63.96 | 148.2 | 10,015.2 | 211 |
| Xero - Support Package [One-Time] | One-time | One-time | 2,608.7 | 2,321.74 | 213.913 | 495.653 | 33,495.71 | 704.35 |
| Xero - Training Package [One-Time] | One-time | One-time | 2,500 | 2,225 | 205 | 475 | 32,100 | 675 |
| Xero - Xero Main Subscription [Annual] | Main | Annual | 4,550 | 4,050 | 373 | 865 | 58,422 | 1,229 |

## Alpha (Xero)
- Category: Accounting
- What it is: Xero delivered by implementation partner Alpha: subscription plus implementation, migration and training.
- Best for: Merchants who want Xero fully set up for them: chart of accounts, templates, integrations.
- Edge: Done-for-you setup and up to 1 year of historical data migration.
- Licensing unit: Basic or Premium Subscription + Additional Branch; Implementation (one-time), Migration Package, Training Sessions.
- Countries: All markets
- Watch out: Don't quote Xero direct and Alpha (Xero) to the same merchant. Pick one route.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - 1 Subscription (Basic / Premium) + (branches − 1) Additional Branch.
  - Implementation is a one-time line.
  - Migration and Training are optional.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Alpha - Xero Basic Subscription - [Annual] | Main | Annual | 2,158 | 2,112 | 178 | 409 | 28,774 | 575 |
| Alpha - Xero Migration Package - [Annual] | Add-on | Annual | 858 | 840 | 71 | 163 | 11,444 | 229 |
| Alpha - Xero Premium Subscription - [Annual] | Main | Annual | 3,242 | 3,173 | 268 | 614 | 43,226 | 865 |
| Alpha - Xero Training Session - [One-time] | One-time | One-time | 1,022 | 1,000 | 84 | 193 | 13,624 | 272.48 |
| Alpha - Xero additional Branch [Annual] | Additional | Annual | 500 | 490 | 41.33 | 94.67 | 6,666.67 | 133.33 |
| Alpha- Xero Implementation - [One-time] | One-time | One-time | 2,044 | 2,000 | 169 | 387 | 27,248 | 545 |

## QuickBooks
- Category: Accounting
- What it is: QuickBooks Online Plus with separate training and support packages.
- Best for: Merchants already on QuickBooks.
- Edge: Familiar to many accountants.
- Licensing unit: Online Plus Subscription + Additional Branch; Training and Support (one-time).
- Countries: All markets
- Watch out: Training and support are not included.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - 1 Subscription + (branches − 1) Additional Branch.
  - Training and Support are separate one-time lines.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| QuickBooks - Online Plus Additional Branch [Annual] | Additional | Annual | 780 | 694.2 | 63.96 | 148.2 | 10,015.2 | 211 |
| QuickBooks - Online Plus Subscription [Annual] | Main | Annual | 4,550 | 4,050 | 373 | 865 | 58,422 | 1,229 |
| QuickBooks - Support Package [One-Time] | One-time | One-time | 2,608.7 | 2,321.74 | 213.913 | 495.653 | 33,495.71 | 704.35 |
| QuickBooks - Training Package [One-Time] | One-time | One-time | 2,500 | 2,225 | 205 | 475 | 32,100 | 675 |

# Category: ERP

How to choose: Pick on size: FlowERP for KSA small and mid-size, SAP or Dynamics for enterprise groups.

## FlowERP
- Category: ERP
- What it is: Finance and ERP that syncs Foodics sales into accounting: automated journals, inventory lifecycle, COGS, ZATCA e-invoicing.
- Best for: KSA small and mid-size groups that need a real ERP without SAP-level cost.
- Edge: Advanced adds assets, production (assembly), waste and payroll. Modular add-ons.
- Licensing unit: Basic or Advanced Package + matching Additional Branch; Implementation per branch (one-time); add-ons (HR, Cost Center, Central Kitchen, B2B Invoicing and more).
- Countries: KSA
- Watch out: Additional Branch must match the package. Implementation is per branch.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLScrAhuEzLPgQIjk01wYfdl5U4MaplE6P-5aTGBzLx4ce3_8Bw/viewform (KSA approval form: Yes)
- Quote structure:
  - 1 Package (Basic / Advanced) + (branches − 1) Additional Branch of the SAME package.
  - Implementation: 1 line per branch (one-time).
  - Add-ons only on request.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| FlowCRM - Lead App - [Annual] | Add-on | Annual | 3,598.8 | 3,524.3 | 296.54 | 679.81 | 48,511.82 | 959.68 |
| FlowChat - Employee Chat App - [Annual] | Add-on | Annual | 4,918.8 | 4,816.98 | 405.31 | 929.16 | 66,305.42 | 1,311.68 |
| FlowERP - Additional Employees - [Annual] | Additional | Annual | 600 | 587.58 | 49.44 | 113.34 | 8,088 | 160 |
| FlowERP - Advanced Inventory - [Annual] | Add-on | Annual | 1,200 | 1,175.16 | 98.88 | 226.68 | 16,176 | 320 |
| FlowERP - Advanced Package (Additional Branch) - [Annual] | Additional | Annual | 2,500 | 2,450 | 205 | 475 | 32,500 | 666.67 |
| FlowERP - Advanced Package - [Annual] | Main | Annual | 4,250 | 4,165 | 348.5 | 807.5 | 55,250 | 1,133.33 |
| FlowERP - B2B Invoicing - [Annual] | Add-on | Annual | 1,200 | 1,175.16 | 98.88 | 226.68 | 16,176 | 320 |
| FlowERP - Basic Package (Additional Branch) - [Annual] | Additional | Annual | 1,171.88 | 1,148.5 | 96.125 | 222.625 | 15,234.38 | 312.5 |
| FlowERP - Basic Package - [Annual] | Main | Annual | 2,450 | 2,401 | 200.9 | 465.5 | 31,850 | 653.33 |
| FlowERP - Central Kitchen - [Annual] | Add-on | Annual | 1,200 | 1,175.16 | 98.88 | 226.68 | 16,176 | 320 |
| FlowERP - Cheques and Withdrawal - [Annual] | Add-on | Annual | 6,000 | 5,875.8 | 494.4 | 1,133.4 | 80,880 | 1,600 |
| FlowERP - Cost Center - [Annual] | Add-on | Annual | 1,560 | 1,528.8 | 120 | 283.64 | 20,280 | 416 |
| FlowERP - HR App - [Annual] | Add-on | Annual | 4,918.8 | 4,816.98 | 405.31 | 929.16 | 66,305.42 | 1,311.68 |
| FlowERP - Implementation Per Branch - [One Time] | One-time | One-time | 937.5 | 918.8 | 76.9 | 178.1 | 12,187.5 | 250 |
| FlowERP - Pre and Scheduled Orders - [Annual] | Add-on | Annual | 1,200 | 1,175.16 | 98.88 | 226.68 | 16,176 | 320 |

## SAP
- Category: ERP
- What it is: SAP Business One for F&B groups: Pro and Limited users, hosting, Foodics integration, maintenance (AMC), implementation.
- Best for: Enterprise and multi-entity groups.
- Edge: Most complete ERP; the B1 Bundle simplifies quoting for a single brand.
- Licensing unit: Users (Pro / Limited: annual, monthly or perpetual one-time) + Hosting + Foodics Integration + AMC + Implementation per engineer-day. B1 Bundle = 1 brand, up to 5 users + 1 indirect user.
- Countries: All markets
- Watch out: Many components. Use the B1 Bundle for a single brand with 5 users or fewer.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - Count Pro and Limited users separately.
  - Always add Hosting + Foodics Integration unless the merchant self-hosts.
  - Implementation is quoted per engineer/day (one-time).

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| SAP - Annual Maintenance Contract (AMC) [Annual] | Add-on | Annual | 0 |  |  |  |  |  |
| SAP - Customer Check Out Retail [Annual] | Main | Annual | 2,250 | 2,250 | 186 | 425.51 |  | 600 |
| SAP - Customer Check Out Retail [Monthly] | Main | Monthly | 187.5 | 187.5 | 15.5 | 35.45 |  | 50 |
| SAP - Foodics Integration [Annual] | Add-on | Annual | 6,750 | 6,750 | 554 | 1,276 |  | 1,800 |
| SAP - Foodics Integration [Monthly] | Add-on | Monthly | 562.5 | 562.5 | 46.17 | 106.37 |  | 150 |
| SAP - HANA Engine [One-Time Fee] | One-time | One-time | 7,500 | 7,500 |  | 1,418.36 |  |  |
| SAP - Hosting [Annual] | Add-on | Annual | 30,000 | 30,000 | 2,460 | 6,000 | 196,850.9 | 8,000 |
| SAP - Hosting [Monthly] | Add-on | Monthly | 2,500 | 2,500 | 205 | 472.78 |  | 666.67 |
| SAP - Implementation (Per Engineer/day) [One-Time Fee] | One-time | One-time | 1,500 | 1,500 | 124 | 283.67 |  | 400 |
| SAP - Limited User [Annual] | Main | Annual | 4,500 | 4,500 | 372 | 849.34 |  | 1,200 |
| SAP - Limited User [Monthly] | Main | Monthly | 375 | 375 | 31 | 70.91 |  | 100 |
| SAP - Limited User [One-Time Fee] | One-time | One-time | 5,250 | 5,250 | 431 | 1,050 | 34,448.91 | 1,400 |
| SAP - Pro User [Annual] | Main | Annual | 6,750 | 6,750 | 558 | 1,274 |  | 1,800 |
| SAP - Pro User [Monthly] | Main | Monthly | 562.5 | 562.5 | 46.5 | 106.37 |  | 150 |
| SAP - Pro User [One-Time Fee] | One-time | One-time | 10,125 | 10,125 | 830 | 2,025 | 66,437.18 | 2,700 |
| SAP B1 Bundle - Annual | Main | Annual | 44,999 | 44,499 | 3,699 | 8,499 | 610,900 | 12,000 |
| SAP Indirect License - Annual | Main | Annual | 1,350 | 1,322 | 110.45 | 255 | 17,046 | 360 |
| SAP Indirect License - Monthly | Main | Monthly | 112 | 110 | 9.2 | 21 | 1,419 | 30 |
| SAP Indirect License - One Time | One-time | One-time | 937.63 | 918.15 | 76.7 | 177 | 11,820 | 250 |

## MS Dynamics
- Category: ERP
- What it is: Microsoft Dynamics 365 Finance with Foodics integration.
- Best for: Groups standardized on Microsoft.
- Edge: Microsoft ecosystem fit.
- Licensing unit: Finance or Premium license + Attach licenses + Team Members + Foodics Integration + Implementation (one-time).
- Countries: All markets
- Watch out: The Foodics Integration line is required for the POS sync.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - Base license (Finance or Premium) + optional Attach and Team Member.
  - Add Foodics Integration and Implementation.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| MS Dynamics - Adding Team Member - [Annual] | Additional | Annual | 432 | 423 | 36 | 82 | 5,760 | 115.2 |
| MS Dynamics - Attach License - [Annual] | Add-on | Annual | 1,620 | 1,585 | 134 | 307 | 21,600 | 432 |
| MS Dynamics - Finance License - [Annual] | Main | Annual | 11,340 | 11,098 | 937 | 2,147 | 151,200 | 3,024 |
| MS Dynamics - Foodics Integration [Annual] | Add-on | Annual | 15,750 | 15,414 | 1,302 | 2,982 | 210,000 | 4,200 |
| MS Dynamics - Implementation - [One-time] | One-time | One-time | 1,200 | 1,174 | 99 | 227 | 16,000 | 320 |
| MS Dynamics - Premium License - [Annual] | Main | Annual | 16,200 | 15,854 | 1,339 | 3,067 | 216,000 | 4,320 |

# Category: E-invoicing & digital receipts

How to choose: Both are licensed per account, not per branch. Pick on terminals and SMS vs invoice volume.

## InvoiceQ
- Category: E-invoicing & digital receipts
- What it is: Compliant B2B and B2C e-invoicing from Foodics POS with tax-authority integration, credit and debit notes, and approval workflows.
- Best for: KSA and Jordan merchants who need ZATCA-compliant invoicing per terminal.
- Edge: Terminal-based model fits merchants with few issuing points.
- Licensing unit: Licensed per account (not per branch). Basic = email only, up to 2 terminals. Advanced = unlimited invoicing + 2,000 SMS/year, per issuing terminal. Customization one-time.
- Countries: KSA, Jordan
- Watch out: Advanced is per issuing terminal. Count terminals, not branches.
- Submit deals with: https://invoiceq.com/?ff_landing=26 (KSA approval form: Yes)
- Quote structure:
  - Basic: one account line covers up to 2 terminals.
  - Advanced: 1 line per issuing terminal.
  - Customization is a one-time line.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| InvoiceQ - Advanced Package - [Annual] | Main | Annual | 3,150 | 2,867 | 240 | 545 | 24,999 | 780 |
| InvoiceQ - Basic Package - [Annual] | Main | Annual | 1,470 | 1,440 | 119.9 | 275 | 14,999 | 390 |
| InvoiceQ - Customization - [One Time] | One-time | One-time | 10,000 | 9,800 | 820 | 1,862 | 124,194 | 2,667 |

## Iisal
- Category: E-invoicing & digital receipts
- What it is: Digital receipts: POS transactions become compliant e-invoices sent by SMS, with sales dashboards, consumer insights and a loyalty program.
- Best for: Merchants who want paperless SMS receipts plus customer insights.
- Edge: Receipts double as a customer-data and loyalty channel. ZATCA Phase 1 and 2.
- Licensing unit: Licensed per account (not per branch). Tier by yearly invoice volume: up to 100, up to 500, 500+.
- Countries: Global
- Watch out: Pick the tier by invoice volume, not by branch count.
- Submit deals with: https://docs.google.com/forms/d/e/1FAIpQLSdmC6bQAoGYvjo-7GKIaGFhQsbp4k-VcH2tPv1xO8sScq4_Fg/viewform (KSA approval form: Yes)
- Quote structure:
  - One account line, tier chosen by invoice volume.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Iisal - B2B E-Invoicing (500+ Invoice) [Annual] | Main | Annual | 6,800 | 6,649 | 557 | 1,284 |  | 1,810 |
| Iisal - B2B E-Invoicing (Up to 100 Invoice) [Annual] | Main | Annual | 1,430 | 1,399 | 117.2 | 270 |  | 380 |
| Iisal - B2B E-Invoicing (Up to 500 Invoice) [Annual] | Main | Annual | 2,725 | 2,664 | 144.7 | 514.4 |  | 725 |

# Category: HR & payroll

How to choose: Both sit on top of SAP. Malachite cannot be sold without SAP.

## VOLT
- Category: HR & payroll
- What it is: HR, payroll, attendance and self-service suite with SAP finance integration.
- Best for: SAP customers who need HR and payroll.
- Edge: Native SAP finance link.
- Licensing unit: Per-module licenses (HR, Payroll, Attendance, ESS, Company Admin, Superuser, Dashboard, Mobile per user) in Annual, Monthly or One-time; Hosting with SAP; Implementation.
- Countries: All markets
- Watch out: Several Monthly lines have inconsistent prices across currencies (flagged ⚠). Verify in Salesforce before quoting.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - Quote per module and per user where the line says per user.
  - Pick one billing model (Annual, Monthly or One-time) for all modules.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| VOLT - Additional Company License with SAP Finance Integration Included [Annual] | Additional | Annual | 630 | 630 | 51.66 | 126 | 4,133.87 | 168 |
| VOLT - Additional Company License with SAP Finance Integration Included [Monthly] | Additional | Monthly | 52.5 | 51 | 4.5 | 9.9 | 702 | 13.9 |
| VOLT - Additional Company License with SAP Finance Integration Included [One-Time Fee] | One-time | One-time | 5,625 | 5,625 | 461 | 1,125 | 36,909.54 | 1,500 |
| VOLT - Attendance License [Annual] | Main | Annual | 23 | 23 | 1.89 | 4.6 | 151.54 | 6 |
| VOLT - Attendance License [Monthly] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | Main | Monthly | 2 | 204.04 | 17.12 | 39.41 | 2,681.55 | 55.56 |
| VOLT - Attendance License [One-Time Fee] | One-time | One-time | 15,750 | 15,750 | 1,292 | 3,150 | 103,346.72 | 4,200 |
| VOLT - Company Admin License [Annual] | Main | Annual | 315 | 315 | 25.83 | 63 | 2,066.93 | 84 |
| VOLT - Company Admin License [Monthly] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | Main | Monthly | 26.25 | 45.91 | 3.85 | 8.87 | 603.35 | 12.5 |
| VOLT - Company Admin License [One-Time Fee] | One-time | One-time | 1,125 | 1,125 | 92 | 225 | 7,381.91 | 300 |
| VOLT - Employee Self Services License [Annual] | Main | Annual | 8 | 8 | 0.66 | 1.6 | 53.12 | 2 |
| VOLT - Employee Self Services License [Monthly] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | Main | Monthly | 0.6 | 30.59 | 2.57 | 5.91 | 402.08 | 8.33 |
| VOLT - Employee Self Services License [One-Time Fee] | One-time | One-time | 19 | 19 | 2 | 3.8 | 124.67 | 5 |
| VOLT - HR License [Annual] | Main | Annual | 23 | 23 | 1.89 | 4.6 | 151.54 | 6 |
| VOLT - HR License [Monthly] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | Main | Monthly | 2 | 15.32 | 1.29 | 2.96 | 201.27 | 4.17 |
| VOLT - HR License [One-Time Fee] | One-time | One-time | 19,500 | 19,500 | 1,599 | 3,900 | 127,953.09 | 5,200 |
| VOLT - Hosting with SAP Included [Annual] | Add-on | Annual | 40,000 |  |  | 7,564.62 |  |  |
| VOLT - Hosting with SAP Included [Monthly] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | Add-on | Monthly | 1,750 | 1,750 |  | 330.95 |  | 5,000 |
| VOLT - Implementation for One-Time Payment Based Deals [One-Time Fee] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | One-time | One-time | 50.63 | 50.63 | 4.15 | 10,125 | 332.19 | 13.5 |
| VOLT - Implementation for Subscription Based Deals [One-Time Fee] | One-time | One-time | 37,500 | 37,500 | 3,075 | 7,500 | 246,063.63 | 10,000 |
| VOLT - Mobile App - per User [Annual] | Add-on | Annual | 8 | 8 | 0.67 | 1.55 | 105.24 | 2.18 |
| VOLT - Mobile App - per User [Monthly] | Add-on | Monthly | 0.5 | 0.66 | 0.06 | 0.13 | 8.69 | 0.18 |
| VOLT - Payroll License [Annual] | Main | Annual | 64 | 64 | 5.25 | 12.8 | 420.26 | 17 |
| VOLT - Payroll License [Monthly] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | Main | Monthly | 5.5 | 45.91 | 3.85 | 8.87 | 603.35 | 12.5 |
| VOLT - Payroll License [One-Time Fee] | One-time | One-time | 28,125 | 28,125 | 2,306 | 5,625 | 184,547.72 | 7,500 |
| VOLT - Upgrade from admin to Superuser Admin License [Annual] | Add-on | Annual | 318.8 | 312.2 | 26.21 | 60.29 | 4,103.94 | 85 |
| VOLT - Upgrade from admin to Superuser Admin License [Monthly] | Add-on | Monthly | 30 | 29.38 | 2.47 | 5.67 | 386.14 | 8 |
| VOLT - Upgrade from admin to Superuser Admin License [One-Time Fee] | One-time | One-time | 1,125.18 | 1,101.81 | 92.47 | 212.79 | 14,480.31 | 300 |
| VOLT -Superuser Admin License [Annual] | Main | Annual | 618 | 624.36 | 52.4 | 120.58 | 8,205.51 | 170 |
| VOLT -Superuser Admin License [Monthly] | Main | Monthly | 51.5 | 52.01 | 4.36 | 10.04 | 683.46 | 14.16 |
| VOLT -Superuser Admin License [One-Time Fee] | One-time | One-time | 2,250.37 | 2,203.62 | 184.94 | 425.58 | 28,960.61 | 600 |
| VOLT – Dashboard [Annual] | Add-on | Annual | 11.25 | 11.02 | 0.92 | 2.13 | 144.81 | 3 |
| VOLT – Dashboard [Monthly] | Add-on | Monthly | 0.94 | 0.92 | 0.08 | 0.18 | 12.06 | 0.25 |
| VOLT – Dashboard [One-Time Fee] ⚠ Prices are inconsistent across currencies in Salesforce. Verify before quoting. | One-time | One-time | 3,375 | 7,345.4 | 616.48 | 1,418.6 | 96,535.37 | 2,000 |
| Volt Performance (Annual) | Add-on | Annual | 11 |  |  | 2.08 |  | 2.93 |
| Volt Performance (Monthly) | Add-on | Monthly | 1 |  |  | 0.18 |  | 0.27 |
| Volt Training (Annual) | Add-on | Annual | 11 |  |  | 2.08 |  | 2.93 |
| Volt Training (Monthly) | Add-on | Monthly | 1 |  |  | 0.18 |  | 0.27 |

## Malachite
- Category: HR & payroll
- What it is: HR, payroll, attendance and employee self-service licenses.
- Best for: SAP customers only.
- Edge: Alternative HR suite for SAP.
- Licensing unit: Per-module annual licenses.
- Countries: All markets
- Watch out: Not a stand-alone solution. It must be activated with SAP.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - Only quote together with SAP.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Malachite - Attendance License  [Annual] | Main | Annual | 27.6 | 27 | 2.3 | 5.2 | 367.8 | 7.4 |
| Malachite - Company Admin License  [Annual] | Main | Annual | 378 | 369.9 | 31.2 | 71.6 | 5,040 | 100.8 |
| Malachite - Employee Self-Service License  [Annual] | Main | Annual | 9.6 | 9.4 | 0.8 | 1.8 | 127.8 | 2.6 |
| Malachite - HR Employees [Annual] | Main | Annual | 129.6 | 120.72 | 10.8 | 24 | 1,728 | 34.8 |
| Malachite - HR License  [Annual] | Main | Annual | 27.6 | 27 | 2.3 | 5.2 | 367.8 | 7.4 |
| Malachite - Payroll License  [Annual] | Main | Annual | 76.5 | 74.9 | 6.3 | 14.5 | 1,020 | 20.4 |

# Category: Table management

How to choose: Only partner in this category.

## Servme
- Category: Table management
- What it is: Reservations and seat management, waitlist, CRM guest profiles and booking widget.
- Best for: Dine-in and fine-dining venues that take reservations.
- Edge: Only table-management partner; flexible billing frequency.
- Licensing unit: Black Plan (Monthly, Quarterly, Semi-annual, Annual) or Advanced Plan (Annual) + one-time Onboarding Fee.
- Countries: All markets
- Submit deals with: Servme Submission Form (KSA approval form: —)
- Quote structure:
  - One plan line + Onboarding Fee on new business.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Servme - Advanced Plan - [Annual] | Main | Annual | 9,288 | 9,089.88 | 767.76 | 1,165.56 | 82,080 | 2,476.8 |
| Servme - Black Plan - [Annual] | Main | Annual | 8,365.56 | 8,187 | 691.56 | 952.56 | 67,080 | 2,230.8 |
| Servme - Black Plan - [Monthly] | Main | Monthly | 697.13 | 682.25 | 57.63 | 79.38 | 5,590 | 185.9 |
| Servme - Black Plan - [Quarterly] | Main | Quarterly | 2,091.38 | 2,046.76 | 172.89 | 238.13 | 16,770 | 557.7 |
| Servme - Black Plan - [Semi Annual] | Main | Semi-annual | 4,182.75 | 4,093.52 | 345.77 | 476.27 | 33,540 | 1,115.4 |
| Servme - Onboarding Fee - [One-Time] | One-time | One-time | 1,443.75 | 1,412.95 | 119.35 | 273.35 | 19,250 | 385 |

# Category: Other

How to choose: Niche or inactive. Confirm with Partnerships before quoting.

## Ishbek
- Category: Other
- What it is: License includes 1 branch.
- Best for: Kuwait or Jordan only.
- Edge: —
- Licensing unit: 1 license per branch.
- Countries: Kuwait, Jordan (priced)
- Watch out: Priced in KWD and JOD only.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - 1 license per branch.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Ishbek - [Annual] | Main | Annual |  |  | 157 | 360 |  |  |
| Ishbek - [Monthly] | Main | Monthly |  |  | 14 | 33 |  |  |

## Roboost
- Category: Other
- What it is: Delivery management system (DMS).
- Best for: Merchants running their own delivery fleet.
- Edge: —
- Licensing unit: Usage-priced line (very small unit price).
- Countries: All markets
- Watch out: Confirm the billing unit with Partnerships before quoting.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - Confirm the unit (per order or per driver) first.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Roboost - DMS Solution | Usage | Usage | 0.3 | 0.24 | 0.021 | 0.045 | 3.25 | 0.07 |

## Nitx — INACTIVE, do not quote
- Category: Other
- What it is: Screen management software.
- Best for: —
- Edge: —
- Licensing unit: Annual license.
- Countries: —
- Watch out: Partner is DEACTIVATED. Do not quote.
- Submit deals with: — (KSA approval form: —)
- Quote structure:
  - Do not quote: partner deactivated.

| Line item (exact Salesforce name) | Type | Billing | KSA (SAR) | UAE (AED) | Kuwait (KWD) | Jordan (JOD) | Egypt (EGP) | International (USD) |
|---|---|---|---|---|---|---|---|---|
| Nitx- SW Only Screen Management [Annual] | Main | Annual | 540 | 529 | 44 | 102 | 4,449 | 149 |
