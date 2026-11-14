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
The owner is whoever the `BRAIN_OWNER_SLACK_ID` secret names. An `owner` line in `layers.yaml` alone gives sales, because this repo is shared.

### Who reads the reply decides the level (`slack-bot/access.py`)
| Where | Answer level |
| --- | --- |
| A partner, a guest (single- or multi-channel), a Slack Connect user, or anyone the bot can't identify asks | Nothing at all, not even a refusal |
| A channel that is Slack Connect (or pending), has any guest or outside member, or matches a partner name pattern | No answer. Only the asker gets a private note |
| Any other channel | The least-privileged member's level, never above **team**. A channel with one Sales member gets a sales answer, even when Kareem asks |
| A DM | The asker's own level. **Owner answers only ever happen in Kareem's DM** |

If Slack can't tell who is asking or who can read the channel, the bot does not answer (fail closed). Replies never carry link or media previews, links to unknown sites are removed, and `@channel`/`@here` are neutralised.

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
Tell it a new or corrected rule. It queues it as owner-only and shows you the fact and an id. Then send:
- `approve <id>` → kept for you only (owner level), live immediately
- `approve <id> team` → shared with the team, live immediately
- `reject <id>` → dropped
- `pending` → list what's waiting
- `reload` → re-read the knowledge files

These commands work only in your DM with the bot. In a channel it tells you privately to DM it.

### Tests
`cd slack-bot && python -m unittest test_brain` (offline, no real accounts needed). 55 tests.

It needs to run somewhere that stays on. Socket Mode means no public URL is needed.

### Deploy on Railway (recommended)
1. railway.app → sign in with GitHub → **New Project → Deploy from GitHub repo** → `The-Counciler-`.
2. Service **Settings → Root Directory** = `reselling-brain`; **Branch** = `claude/reselling-copilot` until PR #5 is merged, then `main`. Railway reads `railway.json` and builds the `Dockerfile` (the build runs the offline tests and fails if they don't pass).
3. **Variables:** add `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `ANTHROPIC_API_KEY`, `BRAIN_OWNER_SLACK_ID=U08DW8E5WKW` and `BRAIN_OWNER_KNOWLEDGE_B64` (Kareem keeps this value; never commit it). Add Salesforce/Google variables later; each tool turns on only when its variables exist.
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
- Approve an exception — it routes every exception to Kareem.
