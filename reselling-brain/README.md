# Reselling Brain: the Foodics Reseller Bot

This folder, in The-Counciler-, is the home of the reseller bot. Everything lives here; nothing is synced to another repo.
**Never change `orbit-reselling-wizard` (Orbit) from this work** (Kareem, 15 Nov 2026).

| Surface | Who | Where |
| --- | --- | --- |
| Slack bot (with layers) | Everyone at Foodics | `slack-bot/`, deployed on Railway from this folder |
| Claude skill (common layer) | Anyone using @Claude in Slack | `sales-skill/`, built by `slack-bot/build_sales_skill.py` |
| Owner skill | Kareem | uploaded in Kareem's own Claude account |
| Web page (built in Orbit, kept as reference) | — | `orbit-web/`: the Ask page, `/api/brain` and Orbit data tools; doesn't run on its own here |

Reports from the build (data issues to fix in Salesforce, the security reviews) are in `reports/`.

All of them read the same files in `knowledge/` (common layer only: how to answer, program overview, line items and quotes, sales scope, working with resellers, cycles at a glance, competitive analysis) and `catalog/` (partner profiles, line items and Salesforce list prices). Policy, partner notes and everything above the common layer come from the Railway secret (see below). To update the brain, edit a file there, then:
- Slack: merge to `main` and Railway redeploys. `reload` (Kareem only, in a DM) re-reads only what the running bot already has (the files in its image, the secret and the learned facts on `/data`).
- Claude skill: run `cd slack-bot && python build_sales_skill.py --zip /tmp` and upload the zip.

## Common-layer skill for @Claude in Slack (no IT approval needed)
The Claude app is already installed in the Foodics Slack. It gives **everyone the same knowledge** (no layers), so it only ever gets the common layer: `sales-skill/reselling-brain-sales/` (the `base` knowledge files plus the catalogue: resellers, list prices, quotes, comparisons, merchant fit, competitive analysis of an offer someone brings, forms, flows). It is built from the bot's own files:
```sh
cd slack-bot && python build_sales_skill.py --zip /tmp   # → /tmp/reselling-brain-sales.zip
```
Upload the zip in claude.ai → Settings → Capabilities → Skills (or ask the Foodics Claude admin to share it with the org). CI fails if the skill is out of date or holds anything above the common layer. **Never** share the owner skill with the org.

## Private knowledge stays out of this repo
This repo is shared with other AI assistants, so it holds the **common layer only** (`base` and `sales`). Team, manager, cost and owner files (policy, discount eligibility, ARR and churn, SLAs, processes, partner notes and channels, cycles and strategy, trackers and contacts, cost prices, contracts, gaps) are **not** committed here. The bot loads them from the Railway secret `BRAIN_OWNER_KNOWLEDGE_B64`: base64 of a JSON list of `{id, body, audience}` with audience `team`, `manager`, `cost` or `owner` (anything else is forced to `owner`), plus one `{"id": "catalog-team-notes", "audience": "team", "catalog": {partner: {slack, watch}}}` item for the team's partner notes. A repo file in `knowledge/` with any other audience is treated as owner-only, and `npm run guard` in `reselling-copilot/` fails the build on it, on `policy.json`/`channels.json`, on partner channel names and on discount bands.

## Audience layers (decided by Kareem, 14 Nov 2026)
| Level | Who | Sees |
| --- | --- | --- |
| everyone (`base`) | every Foodics colleague | Live resellers, list prices by country, how to build the quote, partner comparison (best for, edge, why), merchant fit, competitive analysis (comparing an offer someone brings, pasted or as a file, like for like), submission forms, request flows, unified billing, how a solution operates, and a generic picture of each cycle (it exists, where issues come from, what to take care of) |
| sales | Sales, AMs **and anyone not listed** in `layers.yaml` | The common layer only. Discount rules, cost, contracts, cycles in depth, targets and strategy, contacts, trackers and SLAs are locked: the bot points to the flow and pulls in the right person |
| team | Partnerships team (Althurayyaa) | + policy, discount eligibility, ARR/churn rules, SLAs, processes, partner tiers, channels and notes |
| manager | Managers (Hatem) | + program cycles in depth (why we built it, how it runs now), targets, strategy, internal trackers and partner contacts (Kareem and Hatem only) |
| cost grant | only the Slack IDs in the `BRAIN_COST_SLACK_IDS` secret (Hatem) | + cost prices and contracts, in a private DM only |
| owner | Kareem (the `BRAIN_OWNER_SLACK_ID` secret) | Everything |

Deny by default: a Slack user who is not in `layers.yaml` gets the sales layer. Partners, guests and other workspaces get the **partner** layer only (see below).
The owner and the cost grant come only from Railway secrets. A line in `layers.yaml` alone can't give them, because this repo is shared.

### Triggers: when the bot answers
- A **DM** to the bot.
- An **@mention** in an internal channel. Under a top-level message, the bot reads the message just above the mention (skipping join notices; a Workflow or Dailybot post counts, and so does a shared file). In a thread, it reads the messages posted since its last reply. So `@Reselling Brain` under a question answers that question.
- An **@mention of Kareem** (`BRAIN_OWNER_SLACK_ID`) in any channel or group DM the bot is in (Kareem, 21 Nov 2026). The bot answers first, in the thread, **as the Reselling Brain** (never as Kareem). If the message isn't something it can help with (a personal message, a meeting, thanks, a call only Kareem can make), the model answers `NO_REPLY` and nothing is posted. The bot must be a member of the channel to see the mention, and it can never see DMs sent to Kareem.
- A **follow-up in a thread it already answered in**, without a new mention, for 7 days after its last reply there (`BRAIN_FOLLOW_FILE`, `/data/followed.json` on Railway). It stays quiet when Kareem, Hatem or Althurayyaa write (they are stepping in, and Brain Watch collects it), when the message tags someone else, or when the model answers `NO_REPLY`.

### Hand-offs: who gets pulled in
When part of a question is locked, the bot answers the rest and says "This part I can't answer here". Then it explains the flow to follow and adds the right person under its reply. The @-mentions are added by code from `routing` in `layers.yaml`; the model can't write them.
| Question | Kareem available | Kareem away |
| --- | --- | --- |
| Confidential data or calculations, decisions (cost, margins, discounts, contracts, exceptions, approvals) | @Kareem | @Hatem |
| Operational and day-to-day detail (solution, onboarding, activation, integration, tickets) | @Althurayyaa · cc @Kareem | @Althurayyaa · cc @Hatem |
| Deep cycle questions (exact rules, dates, why a cycle works this way) | @Kareem @Hatem | @Hatem |

"Away" means Kareem sent `away` to the bot in a DM (until `back`), or his Slack status shows leave or sickness (🌴 🏝️ 🏖️ 🤒, or whole words such as vacation, on leave, OOO, إجازة; "back from vacation" and business travel don't count). After `back`, a new leave status counts again. Nobody is pulled in for their own question, and nobody is mentioned twice.

A mention only notifies people who are in the conversation. In a DM, or a channel the person isn't in, the line says so and tells the asker to message them or post in #reseller-hub. (The bot never posts outside the thread it was asked in. The only exception is the 2-week digest DM to Kareem.)

### Who reads the reply decides the level (`slack-bot/access.py`)
| Where | Answer level |
| --- | --- |
| A partner, a guest (single- or multi-channel), a Slack Connect user or someone from another workspace asks | **partner**: the program overview and the answer rules only (`PARTNER_DOCS` in `brain.py`), the `escalate` tool only, and a hard rule against prices, quotes, discounts, cost, margins, commission, contracts, ARR, churn, Salesforce data, internal notes, other partners and promises. These floors are in code, so `layers.yaml` can't widen them |
| A channel that is Slack Connect (or pending), has any guest or outside member, or matches a partner name pattern | **partner** |
| A group DM | Like a private channel: its least-privileged member's level (**partner** if a guest is in it) |
| Someone Slack can't identify, or a bot | Nothing at all |
| A public channel | Always **sales**: every full member can open and search it, even without joining |
| A private channel | The least-privileged member's level, never above **team** (manager, cost and owner answers only in a DM). One Sales member means a sales answer, even when Kareem asks. Deactivated accounts don't count; a deactivated guest still blocks |
| A DM | The asker's own level. **Manager, cost and owner answers only ever happen in a private DM** |

If Slack can't tell who is asking or who can read the channel, the bot does not answer (fail closed). Members and user records are re-checked at least every minute.

Replies never carry link or media previews. A reply may only link to Foodics systems (`*.foodics.com`, the Foodics Slack and Salesforce), Google Drive files (trimmed to the file id), or a link written word for word in `knowledge/` or `catalog/`. Every other link, `mailto:` and bare domain is removed, and `@channel`, `@here`, group and user pings are neutralised.

## Slack bot setup (about 15 minutes)
1. Go to api.slack.com/apps → **Create New App** → **From a manifest** → paste `slack-bot/manifest.yml`. It includes the `users:read` scope, which the bot needs to tell guests and other workspaces apart; without it the bot refuses to start.
2. **Basic Information → App-Level Tokens** → create one with `connections:write` → this is `SLACK_APP_TOKEN`.
3. **Install to Workspace** → copy the Bot token → `SLACK_BOT_TOKEN`.
4. Get an API key at console.anthropic.com → `ANTHROPIC_API_KEY`.
5. Copy `slack-bot/.env.example` to `slack-bot/.env` and fill it in. Put your Slack member ID in `BRAIN_OWNER_SLACK_ID` and in `layers.yaml` as `owner`.
6. Run it:
   ```sh
   cd slack-bot
   pip install -r requirements.txt
   python app.py
   ```
7. Invite the bot to a channel (`/invite @Reselling Brain`) and mention it, or DM it.

### Tools (all read-only, except `learn` and `competitor_quote_save`)
| Tool | Owner (Kareem) | Manager (Hatem) | Team (Althurayyaa) | Sales and everyone else | Setup |
| --- | --- | --- | --- | --- | --- |
| `brain_catalog` | ✅ | ✅ | ✅ | ✅ (discount wording removed) | Nothing extra — reads `catalog/` (list prices only, never cost). `compare` puts 2–4 of our partners side by side |
| `competitor_quotes` | ✅ (+ who reported it) | ✅ (+ who reported it) | ✅ (+ who reported it) | ✅ | Reads the competitor prices colleagues saved, marked merchant-reported and not verified |
| `competitor_quote_save` | ✅ | ✅ | ✅ | ✅ | Saves a competitor's quoted price (competitor, product, country, price, currency, billing) to `BRAIN_COMPETITOR_QUOTES` (`/data/competitor_quotes.json` on Railway, never in git). Refuses our own partners and any cost, margin, markup or commission wording |
| `escalate` | ✅ | ✅ | ✅ | ✅ | Nothing extra — the app adds the @-mentions from `routing` in `layers.yaml` |
| `read_slack_file` | ✅ | ✅ | ✅ | ✅ | Opens only files attached to the message being answered (or to the message just above a bare mention), e.g. an offer to compare |
| `sheets_read` | ✅ all listed sheets | ✅ sheets marked `audience: team` or `audience: manager` (trackers) | ✅ only sheets marked `audience: team` | — | Google service-account key in the `GOOGLE_SERVICE_ACCOUNT_JSON` secret (never commit the key file) + list the real sheets in a server-side copy of `layers.yaml` (point `BRAIN_LAYERS_FILE` at it on the `/data` volume; never in this repo) and share them with the service account |
| `salesforce_find` | ✅ | ✅ | ✅ | ✅ (not partners) | Finds an account or opportunity by name and returns only its name, type and Salesforce link (up to 5), so replies can link the right record. Same `SF_*` variables |
| `salesforce_query` | ✅ | — | — | — | `SF_*` variables: a dedicated **read-only** integration user (API enabled), set only in Railway |
| `drive_search` / `drive_read` | ✅ | — | — | — | Same Google key; share the folder with it and put its id in the `BRAIN_DRIVE_FOLDERS` secret (comma-separated, never in the repo). Without it `drive_search` is off |
| `slack_read_channel` | ✅ (not DMs) | — | — | — | The bot reads only channels it was invited to. Partner messages are data, never instructions |
| `learn` | ✅ | — | — | — | Nothing extra |

A tool turns itself on only when its credentials are set, so you can start with Slack only and add Salesforce and Google later.
Each level's tools are listed in `layers.yaml` (`levels.<level>.tools`). `TOOL_MIN_LEVEL` in `slack-bot/brain.py` sets hard floors that `layers.yaml` can't lower: Salesforce, Drive, `slack_read_channel` and `learn` are owner-only, and `sheets_read` needs team or above. In a channel the level is never above team, so manager sheets open only in a DM.

### Teaching the bot (Kareem only, in a DM)
Tell it a new or corrected rule. It queues it as owner-only, and the bot adds the exact stored text and id under its reply (so you never approve the model's paraphrase). Then send:
- `approve <id>` → kept for you only (owner level), live immediately
- `approve <id> team` → shared with the team, live immediately. Facts about cost, margin, markup, commission, contracts, targets or strategy are refused and stay pending
- `reject <id>` → dropped
- `pending` → list what's waiting
- `quotes csv` → the competitor prices colleagues saved, as CSV (fixed columns; rows that read like cost are never exported)
- `drop quote <id>` → remove a wrong competitor price
- `reload` → re-read the knowledge files
- `away` / `back` → hand decisions to Hatem while you're off, then take them back
- `status` → shows whether the bot thinks you're away, and why

These commands work only in your DM with the bot. In a channel it tells you privately to DM it.

### Brain Watch: gaps and corrections (Kareem only, in a DM)
The bot logs every answer it gives (on the `/data` volume, never in git) so you can see where it fell short:
- **Someone stepped in:** in a channel thread the bot answered, you, Hatem or Althurayyaa (`routing` in `layers.yaml`) wrote after its reply, and weren't the asker or asking the bot again. You decide in `review` whether it was a real correction.
- **Asked without an answer or a clear answer:** the bot handed off, said a part is locked, said it isn't in the brain yet, or failed. Grouped by similar wording, most asked first.
- **Your notes:** anything you add yourself.

Commands:
- `review` → re-reads the threads of the last 14 days, then shows the three lists with ids and thread links
- `digest` → the 2-week digest: insights (answers, share without a clear answer, response time, where, who asks most by Slack title or level, top askers, most asked questions), then the review. Nothing goes into the brain until you `teach` and `approve` it
  - The bot also DMs you the digest on its own **every other Sunday at 11:30 Riyadh time**, starting Sunday 22 Nov 2026 (Kareem, 16 Nov 2026). It's the only message the bot starts itself, and it only goes to you. If the bot was down at 11:30 it sends it when it's back, the same day only.
- `note <text>` → adds your own note (a DM that starts with `note ` is always taken as a note)
- `teach <id>` → turns a correction or a note into a learn proposal; then `approve <id>` / `approve <id> team` as usual
- `dismiss <id>` → drops an item from the review

It uses the scopes the bot already has: no new Slack events and no reinstall. DMs can't have someone step in, so only their unanswered questions show. Answers older than 60 days are dropped. On Railway set `BRAIN_WATCH_FILE=/data/watch.json`.

### Tests
`cd slack-bot && python -m unittest test_brain test_app` (offline, no real accounts needed). 141 tests (112 in `test_brain`, 29 in `test_app`). `test_app` drives `app.py` with every Slack call faked; the Docker build runs both.

It needs to run somewhere that stays on. Socket Mode means no public URL is needed.

### Deploy on Railway (recommended)
1. railway.app → sign in with GitHub → **New Project → Deploy from GitHub repo** → `The-Counciler-`.
2. Service **Settings → Root Directory** = `reselling-brain`; **Branch** = `main`. Railway builds the `Dockerfile` in that folder (the build runs the offline tests and fails if they don't pass). Set the builder (Dockerfile) and the restart policy (On Failure) in Railway **Settings**: Railway doesn't read `railway.json` from a root directory, and stops reading config files on 1 Dec 2026.
3. **Variables:** add `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `ANTHROPIC_API_KEY`, `BRAIN_OWNER_SLACK_ID=U08DW8E5WKW`, `BRAIN_COST_SLACK_IDS=U02VD9VGNA0` and `BRAIN_OWNER_KNOWLEDGE_B64` (Kareem keeps this value; never commit it). Add a **volume mounted at `/data`** (keep 1 replica) for state that must survive deploys: `BRAIN_STATE_FILE=/data/state.json` (away/back), `BRAIN_LEARN_QUEUE=/data/learn_queue.json`, `BRAIN_OWNER_LEARNED_FILE=/data/learned_owner.md`, `BRAIN_TEAM_LEARNED_FILE=/data/learned_team.md`, `BRAIN_COMPETITOR_QUOTES=/data/competitor_quotes.json`, `BRAIN_WATCH_FILE=/data/watch.json` (Brain Watch log), `BRAIN_FOLLOW_FILE=/data/followed.json` (threads it follows). `BRAIN_DRIVE_FOLDERS` holds the Drive folder ids Kareem's Drive tools may search (Kareem keeps the value). Add Salesforce/Google variables later; each tool turns on only when its variables exist. Optional: `BRAIN_MAX_TOKENS` (default 4000).
4. Deploy. The log shows `Private knowledge loaded: … team, … manager, … cost, … owner docs, team notes for … partners.` (counts only), `Tools enabled: …` and `⚡️ Bolt app is running!`. If it says the secret is not set or can't be read, set it again from Kareem's copy.

Note: learned facts and the learn queue live on the `/data` volume and survive deploys. None of them is written to `knowledge/`.
- Team facts (`approve <id> team`, in `/data/learned_team.md` on Railway, `slack-bot/learned_team.md` locally): add them to the team part of the `BRAIN_OWNER_KNOWLEDGE_B64` secret when you want them permanent.
- Owner facts (`approve <id>`, in `/data/learned_owner.md` on Railway, `slack-bot/learned_owner.md` locally, never in `knowledge/`): add them to the `BRAIN_OWNER_KNOWLEDGE_B64` secret when you want them permanent. **Never commit them.** The local files are in `.gitignore` and `.dockerignore`. Facts about cost, margin, markup, commission, contracts, targets or strategy can't be shared with the team.

## What the bot will never do
- Give a partner, a guest or a user from another workspace more than the partner layer, in a DM or anywhere else.
- Answer above the partner layer in a channel partners can read: per-partner channels (`#ksa-…`, `#uae-…`, `#egypt-…`, `#kw-jo-…`, `#kw-…`, `#jo-…`, `#eg-…`), `#foodics-…`, any Slack Connect channel (or one with a pending invite), or any channel with a guest or outside member. Patterns live in `layers.yaml` (`blocked_channels`, `allowed_channels`).
- Post as Kareem or any other person. It always posts as the Reselling Brain bot.
- Post an owner or team answer where a lower level can read it.
- Post outside the thread it was asked in (except the 2-week digest DM to Kareem).
- Message a partner or a merchant.
- Approve an exception: it points to the flow and pulls in Kareem (Hatem when Kareem is away).
- Answer in a channel unless the bot or Kareem is mentioned, or it is a follow-up in a thread the bot answered in.
