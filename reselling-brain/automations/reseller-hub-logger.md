# Reseller Hub logger (scheduled task)

**Status: paused.** The live task is "Reseller Hub: log & flag new requests" in Kareem's Claude scheduled tasks (hourly at :22 when on). This file is a safe copy of how it works so everything about the reseller bot lives in one repo. Editing this file does not change the task.

**Not in this file:** the policy checks (discount eligibility, refund and change windows, compensation rules, currency and escalation rules). They are team-level, so they stay in the scheduled task itself and in the Brain's Railway secret (`BRAIN_OWNER_KNOWLEDGE_B64`), never in this repo.

## What it does
Every run it reads the private Slack channel **#reseller-hub**, logs new requests in Kareem's sheet, follows up on open ones, and sends Kareem a short phone summary.

## Hard rules
- Read-only on Slack: never posts, replies, reacts, DMs, edits or deletes. Never emails anyone.
- Never approves, rejects or decides anything. Every decision is Kareem's.
- Writes only to the one log sheet (append rows, update cells of existing rows).
- Never shows costs, markups or partner pricing.
- If a tool fails, it doesn't guess; it says so in the final message.

## Log sheet
"Reseller Hub Log", tab `Requests`, columns A–AD:
Request ID, Submitted at, Submitted by, Request type, Country, Partner, F5 number, CR number, Brand, Branch count, Discount %, Scope, Expansion plan, New business?, Salesforce opportunity, Rule being excepted, Justification, Evidence link, Invoice date, Question, Urgent?, Urgency reason, Slack thread link, Status, Decision, Decision reason, Decided by, Decision date, Response due by, SLA met?.
Column W (Slack thread link) marks a request as already logged.

## Steps
1. **Read** #reseller-hub for the last 7 days (limit 100). Skip join/leave, system and bot messages.
2. **New requests** = top-level messages from anyone but Kareem whose permalink is not in column W. For each:
   - Type: **Discount**, **Exception** (refund, downgrade, cancellation, compensation, extension, anything outside policy) or **Question**.
   - Pull every field from the message and its thread.
   - Required fields. All: Country, Partner, F5 number, Brand. Discount: CR number, Branch count, Discount %, Scope, Expansion plan, New business?, Salesforce opportunity link. Exception: exception type, rule broken, Invoice date, Justification, Evidence link. Question: the question.
   - Policy flags: checked against the Reseller Program policy (kept outside this repo, see above). Flag only, never decide.
   - Response due by: 24 working hours if urgent, else 48. Working days Sunday–Thursday, Asia/Riyadh.
   - Append a row: Request ID `RH-YYYYMMDD-NN`, the fields, Status `Open` (`Pending` if fields are missing), Slack thread link, Response due by.
3. **Updates** for rows not `Closed`: re-read the thread, fill fields added later (back to `Open` when complete). If Kareem replied with a decision (approved / rejected / need info / escalated / answered, English or Arabic), set Decision, Decision reason, Decided by = Kareem, Decision date, Status `Closed` (`Pending` for need info) and SLA met?. Past Response due by with no decision: Status `Due` (`Urgent` if urgent).
4. **Final message** for Kareem's phone, short English. Nothing new and nothing due: no message. Otherwise each new request (ref, type, requester, brand, one-line ask, missing fields, policy flags) with a ready-to-paste thread reply in the requester's language, then Due/Urgent requests waiting on him, then any errors.
