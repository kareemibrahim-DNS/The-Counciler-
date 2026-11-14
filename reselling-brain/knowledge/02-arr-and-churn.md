---
id: arr-and-churn
audience: team
updated: 2026-11-14
---
# ARR and churn rules

## ARR transaction types
New business, Renewal, Expansion, Churn, Reactivation.
- Opening balance is zero; tracked monthly.
- A downgrade counts as Churn.
- Salesforce churn is final and counted as is.
- Official source: Salesforce report "Monthly ARR – Countries" (Total ARR field). A daily Salesforce export holds every transaction, including reactivations.

## "New ARR" (reseller team definition)
New Business + Expansion + Re-Activation. Excludes renewal and churn.

## Renewal churn — grace period by merchant tier
Counted as lost only after the grace period ends:
| Tier | Grace period |
| --- | --- |
| White glove | 45 days |
| Key account | 30 days |
| SME | 15 days |
| Low touch | 5 days |

- During the grace period the merchant is still active (not churn).
- If he pays after grace ends he is reactivated. The restored ARR reverses the churn **only if paid in the same quarter**.
- Reactivation paid in a later quarter than the churn: Kareem supplies the Salesforce reason per deal. There is no fixed rule — ask Kareem.

## Sales churn
- Counts as churn only if the merchant churns **within 30 days**.
- After 30 days it needs Kareem's approval: approved → lost; not approved → ARR stays counted in full but highlighted.

## Billing timing
- Renewal invoices are issued **3 months before** the renewal date. They are recorded in the system but exported only for the period that is available.
