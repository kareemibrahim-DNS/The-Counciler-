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

## Owner-only knowledge stays out of this repo
This repo is shared with other AI assistants. The owner files (pricing and markups, targets and strategy, partner contacts and trackers, gaps) are **not** committed here. The bot loads them from the Railway secret `BRAIN_OWNER_KNOWLEDGE_B64` (base64 of a JSON list of `{id, body}`); every doc loaded that way is forced to `audience: owner`. `npm run guard` in `reselling-copilot/` fails the build if an owner file or a markup table ever lands in `knowledge/`.

## Audience layers (decided by Kareem, 14 Nov 2026)
Each knowledge file has `audience: owner`, `team` or `sales`.
| Level | Who | Sees |
| --- | --- | --- |
| owner | Kareem | Everything (owner + team files) |
| team | Partnerships team and managers (e.g. Hatem), listed in `layers.yaml` | Team files only: no partner contacts, trackers, contract status, pricing/markups, targets or strategy |
| sales | Sales and AMs, **and anyone not listed** in `layers.yaml` | Only the `sales-scope` file and a limited catalogue: available resellers, list prices, commercial structure |

Deny by default: a Slack user who is not in `layers.yaml` gets the sales layer. Partners in Orbit get no access.

## Slack bot setup (about 15 minutes)
1. Go to api.slack.com/apps → **Create New App** → **From a manifest** → paste `slack-bot/manifest.yml`.
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
| `sheets_read` | ✅ all listed sheets | ✅ only sheets marked `audience: team` | Google service-account key + list the sheets in `layers.yaml` and share them with the service account |
| `drive_search` / `drive_read` | ✅ | — | Same key; share the "Partnerships - Reseller Program" folder with it |
| `slack_read_channel` | ✅ | ✅ | Invite the bot to the partner channels it should read |
| `read_slack_file` | ✅ | ✅ | Nothing extra — attach a PDF/Excel/Word/CSV to the message |
| `learn` | ✅ | — | Nothing extra |
| `brain_catalog` | ✅ | ✅ | Nothing extra — reads `catalog/` (list prices only, never cost) |

A tool turns itself on only when its credentials are set, so you can start with Slack only and add Salesforce and Google later.
Which level gets which tool is set in `layers.yaml` (we finalize it when we define the layers).

### Teaching the bot (Kareem only)
Tell it a new or corrected rule. It queues it and replies with an id. Then send:
- `approve <id>` → saved to the knowledge and live immediately
- `reject <id>` → dropped
- `pending` → list what's waiting
- `reload` → re-read the knowledge files

### Tests
`cd slack-bot && python -m unittest test_brain` (offline, no real accounts needed). 21 tests.

It needs to run somewhere that stays on. Socket Mode means no public URL is needed.

### Deploy on Railway (recommended)
1. railway.app → sign in with GitHub → **New Project → Deploy from GitHub repo** → `The-Counciler-`.
2. Service **Settings → Root Directory** = `reselling-brain`; **Branch** = `claude/reselling-copilot` until PR #5 is merged, then `main`. Railway reads `railway.json` and builds the `Dockerfile` (the build runs the offline tests and fails if they don't pass).
3. **Variables:** add `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `ANTHROPIC_API_KEY`, `BRAIN_OWNER_SLACK_ID=U08DW8E5WKW` and `BRAIN_OWNER_KNOWLEDGE_B64` (Kareem keeps this value; never commit it). Add Salesforce/Google variables later; each tool turns on only when its variables exist.
4. Deploy. The log shows `Tools enabled: …` and `⚡️ Bolt app is running!`.

Note: facts approved with `approve <id>` are written inside the running container and are lost on the next deploy. Copy approved facts into `knowledge/` with a PR to keep them.

## What the bot will never do
- Answer in a channel partners can read: per-partner channels (`#ksa-…`, `#uae-…`, `#egypt-…`, `#kw-jo-…`), `#foodics-…`, any Slack Connect channel, or a user from another workspace. It asks people to DM it instead. Patterns live in `layers.yaml` (`blocked_channels`, `allowed_channels`).
- Post outside the thread it was asked in.
- Message a partner or a merchant.
- Approve an exception — it routes every exception to Kareem.
