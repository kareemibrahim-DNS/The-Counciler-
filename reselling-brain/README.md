# Reselling Brain

One brain for the Foodics Reseller Program, used in three places:

| Surface | Who | Folder |
| --- | --- | --- |
| Claude Skill | Kareem | saved from the review card in Claude |
| Slack bot | The team | `slack-bot/` |
| Orbit | Orbit users | `orbit-reselling-wizard` (`/api/brain` + `reselling-brain.html`), built from a copy of these files |

All three read the same files in `knowledge/` (rules, policy, partners) and `catalog/` (line items and Salesforce list prices). To update the brain, edit a file there, then:
- Slack: send `reload` to the bot (Kareem only), or restart it.
- Orbit: copy the changed files to `orbit-reselling-wizard/reselling-brain/`, run `node scripts/build-brain-knowledge.mjs` there and open a PR.
- Skill: ask Claude to update the Reselling Brain skill.

## Common-layer skill for @Claude in Slack (no IT approval needed)
The Claude app is already installed in the Foodics Slack. It gives **everyone the same knowledge** (no layers), so it only ever gets the common layer: `sales-skill/reselling-brain-sales/` (the `base` knowledge files plus the catalogue: resellers, list prices, quotes, comparisons, merchant fit, forms, flows). It is built from the bot's own files:
```sh
cd slack-bot && python build_sales_skill.py --zip /tmp   # → /tmp/reselling-brain-sales.zip
```
Upload the zip in claude.ai → Settings → Capabilities → Skills (or ask the Foodics Claude admin to share it with the org). CI fails if the skill is out of date or holds anything above the common layer. **Never** share the owner skill with the org.

## Private knowledge stays out of this repo
This repo is shared with other AI assistants. Manager, cost and owner files (cycles and strategy, trackers and contacts, cost prices, contracts, gaps) are **not** committed here. The bot loads them from the Railway secret `BRAIN_OWNER_KNOWLEDGE_B64` (base64 of a JSON list of `{id, body, audience}`, audience `manager`, `cost` or `owner`; anything else is forced to `owner`). `npm run guard` in `reselling-copilot/` fails the build if a file in `knowledge/` has any audience other than `base`, `sales` or `team`, or looks like a markup table or targets.

## Audience layers (decided by Kareem, 14 Nov 2026)
| Level | Who | Sees |
| --- | --- | --- |
| everyone (`base`) | every Foodics colleague | Live resellers, list prices by country, how to build the quote, partner comparison (best for, edge, why), merchant fit, submission forms, request flows, unified billing, how a solution operates |
| sales | Sales, AMs **and anyone not listed** in `layers.yaml` | The common layer only. Discount rules, cost, contracts, cycles, contacts, trackers and SLAs are locked: the bot points to the flow and pulls in the right person |
| team | Partnerships team (Althurayyaa) | + policy, discount eligibility, ARR/churn rules, SLAs, processes, partner tiers, channels and notes |
| manager | Managers (Hatem) | + program cycles (why we built it, how it runs now), targets, strategy, internal trackers, partner contacts |
| cost grant | only the Slack IDs in the `BRAIN_COST_SLACK_IDS` secret (Hatem) | + cost prices and contracts, in a private DM only |
| owner | Kareem (the `BRAIN_OWNER_SLACK_ID` secret) | Everything |

Deny by default: a Slack user who is not in `layers.yaml` gets the sales layer. Partners in Orbit get no access.
The owner and the cost grant come only from Railway secrets. A line in `layers.yaml` alone can't give them, because this repo is shared.

### Triggers: when the bot answers
- A **DM** to the bot.
- An **@mention** in an internal channel. The bot reads the message just above the mention (or the thread it is in), so `@Reselling Brain` under a question answers that question. Without a mention it never answers in a channel.

### Hand-offs: who gets pulled in
When a question needs a person, the bot explains the flow to follow and adds the right person under its reply. The @-mentions are added by code from `routing` in `layers.yaml`; the model can't write them.
| Question | Kareem available | Kareem away |
| --- | --- | --- |
| Decision (discounts, exceptions, approvals, cost, contracts) | @Kareem | @Hatem |
| Operational detail (solution, onboarding, activation, integration, tickets) | @Althurayyaa · cc @Kareem | @Althurayyaa · cc @Hatem |

"Away" means Kareem sent `away` to the bot in a DM (until `back`), or his Slack status shows leave, travel or sickness (🌴 ✈️ 🏝️ 🤒, or words such as vacation, leave, OOO, إجازة). Nobody is pulled in for their own question.

### Who reads the reply decides the level (`slack-bot/access.py`)
| Where | Answer level |
| --- | --- |
| A partner, a guest (single- or multi-channel), a Slack Connect user, or anyone the bot can't identify asks | Nothing at all, not even a refusal |
| A channel that is Slack Connect (or pending), has any guest or outside member, or matches a partner name pattern | No answer. Only the asker gets a private note |
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

### Tools (all read-only)
| Tool | Kareem | Team (for now) | Setup |
| --- | --- | --- | --- |
| `salesforce_query` | ✅ | — | `SF_*` in `.env` (read-only integration user recommended) |
| `sheets_read` | ✅ all listed sheets | ✅ only sheets marked `audience: team` (trackers are owner-only) | Google service-account key in the `GOOGLE_SERVICE_ACCOUNT_JSON` secret (never commit the key file) + list the sheets in `layers.yaml` and share them with the service account |
| `drive_search` / `drive_read` | ✅ | — | Same key; share the "Partnerships - Reseller Program" folder with it |
| `slack_read_channel` | ✅ (not DMs) | — | The bot reads only channels it was invited to. Partner messages are data, never instructions |
| `read_slack_file` | ✅ | ✅ | Opens only files attached to the message being answered |
| `learn` | ✅ | — | Nothing extra |
| `brain_catalog` | ✅ | ✅ | Nothing extra — reads `catalog/` (list prices only, never cost) |

A tool turns itself on only when its credentials are set, so you can start with Slack only and add Salesforce and Google later.
Which level gets which tool is set in `layers.yaml` (we finalize it when we define the layers).

### Teaching the bot (Kareem only, in a DM)
Tell it a new or corrected rule. It queues it as owner-only, and the bot adds the exact stored text and id under its reply (so you never approve the model's paraphrase). Then send:
- `approve <id>` → kept for you only (owner level), live immediately
- `approve <id> team` → shared with the team, live immediately. Facts about cost, margin, markup, wholesale, payout or commission are refused and stay pending
- `reject <id>` → dropped
- `pending` → list what's waiting
- `reload` → re-read the knowledge files
- `away` / `back` → hand decisions to Hatem while you're off, then take them back
- `status` → shows whether the bot thinks you're away, and why

These commands work only in your DM with the bot. In a channel it tells you privately to DM it.

### Tests
`cd slack-bot && python -m unittest test_brain test_app` (offline, no real accounts needed). 86 tests. `test_app` drives `app.py` with every Slack call faked; the Docker build runs both.

It needs to run somewhere that stays on. Socket Mode means no public URL is needed.

### Deploy on Railway (recommended)
1. railway.app → sign in with GitHub → **New Project → Deploy from GitHub repo** → `The-Counciler-`.
2. Service **Settings → Root Directory** = `reselling-brain`; **Branch** = `claude/reselling-copilot` until PR #5 is merged, then `main`. Railway reads `railway.json` and builds the `Dockerfile` (the build runs the offline tests and fails if they don't pass).
3. **Variables:** add `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `ANTHROPIC_API_KEY`, `BRAIN_OWNER_SLACK_ID=U08DW8E5WKW`, `BRAIN_COST_SLACK_IDS=U02VD9VGNA0` and `BRAIN_OWNER_KNOWLEDGE_B64` (Kareem keeps this value; never commit it). Add Salesforce/Google variables later; each tool turns on only when its variables exist.
4. Deploy. The log shows `Tools enabled: …` and `⚡️ Bolt app is running!`.

Note: approved facts are written inside the running container and are lost on the next deploy.
- Team facts (`approve <id> team`, in `knowledge/10-learned-team.md`): copy them into the right team file in `knowledge/` with a PR.
- Owner facts (`approve <id>`, in `slack-bot/learned_owner.md`, outside `knowledge/`): add them to the `BRAIN_OWNER_KNOWLEDGE_B64` secret. **Never commit them.** Both files are in `.gitignore` and `.dockerignore`.

## What the bot will never do
- Answer a partner, a guest or a user from another workspace, in a DM or anywhere else.
- Answer in a channel partners can read: per-partner channels (`#ksa-…`, `#uae-…`, `#egypt-…`, `#kw-jo-…`), `#foodics-…`, any Slack Connect channel (or one with a pending invite), or any channel with a guest or outside member. Patterns live in `layers.yaml` (`blocked_channels`, `allowed_channels`).
- Post an owner or team answer where a lower level can read it.
- Post outside the thread it was asked in.
- Message a partner or a merchant.
- Approve an exception: it points to the flow and pulls in Kareem (Hatem when Kareem is away).
- Answer in a channel without being mentioned.
