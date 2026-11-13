# AI Council — Project Spec

Personal app for one user (Kareem). He sends an idea; a "council" of AI models handles it; the best-suited one replies with an execution plan (steps 1, 2, 3). The app also shows how much prepaid API balance is left per provider and when it will run out at the current burn rate.

Read this whole file before writing code. The UI copy is Arabic (RTL); code, comments and identifiers are English.

---

## 1. Surfaces

1. **PWA** (installable web app on the phone home screen). Two screens + settings:
   - **المجلس (Council):** idea input → response → plan.
   - **الرصيد (Usage):** remaining balance %, daily burn, days left — total and per provider.
   - **الإعدادات (Settings):** budgets, model per role, Slack status.
2. **Slack** (primary daily surface): Kareem DMs the bot or mentions it in a channel → the council replies **in the thread**.

Both surfaces call the same backend. No logic lives in the browser.

## 2. Architecture

```
PWA (Cloudflare Pages)  ─┐
                         ├──► Worker API (Cloudflare Workers) ──► Claude / OpenAI / DeepSeek / xAI APIs
Slack Events API  ───────┘            │
                                      └──► D1 (history, usage ledger) + KV (sessions)
```

- **Frontend:** Vite + React + TypeScript, `vite-plugin-pwa` (manifest, icons, offline shell). RTL, Arabic.
- **Backend:** one Cloudflare Worker (Hono). All API keys live in Worker **secrets** — never in the frontend, never in git.
- **Storage:** D1 for `runs`, `responses`, `usage_ledger`, `budgets`; KV for login sessions.
- **Repo layout:** `apps/web` (PWA), `apps/worker` (API + Slack), `packages/shared` (types, prompts, price table).

## 3. The council

### Members and roles (configurable in Settings, stored in D1)

| Member   | Default role (Arabic label) | Strength used for                  |
|----------|-----------------------------|------------------------------------|
| Claude   | الاستراتيجي                  | planning, strategy, structure      |
| ChatGPT  | الكاتب                       | writing, messaging, copy           |
| DeepSeek | المحلل                       | numbers, analysis, logic           |
| Grok     | الترندات                     | current events, market signals     |

Copilot has no personal API → shown in the UI as "not connected", never called.

**Model IDs are env vars**, not hardcoded: `MODEL_CLAUDE`, `MODEL_OPENAI`, `MODEL_DEEPSEEK`, `MODEL_XAI`, `MODEL_JUDGE`. Use each provider's official API (Anthropic Messages, OpenAI, DeepSeek's OpenAI-compatible endpoint, xAI's OpenAI-compatible endpoint).

### Two modes

- **الأنسب يرد (Best fit — default):**
  1. Judge (cheap model, `MODEL_JUDGE`) gets the idea + the roles table and returns JSON `{ "winner": "claude|openai|deepseek|xai", "reason": "..." }`.
  2. Only the winner is called. It must return the plan format below.
- **الكل يرد (Everyone):**
  1. All four called in parallel (`Promise.allSettled`, 45 s timeout each; a failed member is shown as unavailable, not a crash).
  2. Judge merges them into one plan and picks whose answer was strongest.

### Plan output format (all members, enforced by the system prompt, parsed as JSON)

```json
{
  "summary": "one line in Egyptian Arabic",
  "steps": ["step 1", "step 2", "step 3"],
  "notes": "optional short caveat"
}
```
3 to 5 steps. Reply language follows the user's message (Arabic in → Arabic out). If JSON parsing fails, show the raw text — never drop the answer.

## 4. Slack (option أ: write the idea in Slack, the council answers there)

- Slack app with bot scopes: `app_mentions:read`, `im:history`, `chat:write`. Events: `app_mention`, `message.im`.
- `POST /slack/events` on the Worker:
  - Verify `X-Slack-Signature` with `SLACK_SIGNING_SECRET` (reject anything older than 5 minutes).
  - Handle `url_verification`.
  - **Ack within 3 seconds** (return 200 immediately), then do the work in `ctx.waitUntil(...)`.
  - Ignore retries (`X-Slack-Retry-Num` header) and bot messages, so nothing runs twice.
  - **Allow-list:** only `SLACK_ALLOWED_USER_ID` (Kareem). Anyone else gets no reply.
- Flow: post "⏳ المجلس بيفكر…" in the thread → run the council → `chat.update` that message with the result (winner, reason, numbered steps).
- Text starting with `الكل:` or `all:` → Everyone mode. Otherwise Best fit.
- Every Slack run is saved in D1 and appears in the PWA history.

## 5. Usage and forecast

Prepaid API balance per provider, plus a forecast.

1. **Ledger (always on, the source of truth):** every API call records `provider, model, input_tokens, output_tokens, cost_usd, created_at`. Cost = token counts from the API response × the price table in `packages/shared/prices.ts` (editable; prices change).
2. **Budgets:** Kareem enters the amount he loaded per provider and the date (Settings). `remaining = budget − spent since that date`.
3. **Provider reconciliation (where the provider exposes it):**
   - DeepSeek: `GET /user/balance` → real balance; prefer it over the ledger.
   - Anthropic and OpenAI: their cost/usage reports need an **admin** key. Optional: if `ANTHROPIC_ADMIN_KEY` / `OPENAI_ADMIN_KEY` is set, a daily cron reconciles; if not, the ledger is used.
   - xAI: ledger only unless an official balance endpoint is confirmed.
4. **Forecast:** `daily_burn = spend over the last 7 days ÷ 7` (fewer days if less history). `days_left = remaining ÷ daily_burn`. Show "حوالي N يوم" and the date.
5. **Alerts in the app:** a banner when any provider is below 20% or under 5 days left. (Slack alerts = option ب, later.)

Subscriptions (Claude Pro, ChatGPT Plus, etc.) are **not** tracked — providers don't expose them.

## 6. Security

- PWA is locked: a passcode → Worker sets an HttpOnly session cookie (KV, 30 days). Optional WebAuthn (Face ID) later.
- Secrets only via `wrangler secret put`. `.dev.vars` is git-ignored. Add a `.env.example` listing names only.
- Rate limit: 30 council runs per hour.
- Never log prompt text or keys in plain Worker logs.

## 7. UI

The approved mockups are in `design/Main.dc.html` (Council) and `design/Usage.dc.html` (Usage). Match them:
- Dark: background `#0E0F13`, cards `#171920`, borders `#2A2D37`, text `#F2F2F4`, muted `#A3A6B1`, accent `#3DD6B5`, warning `#F2C48D`, danger `#FF8A7A`.
- Fonts: IBM Plex Sans Arabic (Arabic), Inter (Latin, numbers).
- Member colors: Claude `#D97757`, ChatGPT `#74C69D`, DeepSeek `#7AA2FF`, Grok `#E9E9EC`.
- Bottom tab bar: المجلس / الرصيد / الإعدادات. Touch targets ≥ 44 px. `dir="rtl"`.
- Loading states per member, empty states, error states.

## 8. Build order (one PR each, small)

1. Monorepo scaffold, PWA shell with the 3 tabs and static screens matching the design.
2. Worker skeleton + D1 schema + passcode login.
3. Provider clients + Best-fit mode end to end in the PWA.
4. Everyone mode + history.
5. Slack events endpoint (section 4).
6. Usage ledger, budgets, forecast, Usage screen live (section 5).
7. Deploy: Pages + Worker, custom domain optional, install on the phone.

## 9. Definition of done (each PR)

- `npm run typecheck` and `npm run build` pass.
- No secrets in the diff.
- PR description lists what changed and how to test it.
- Kareem reviews and merges. Never merge or deploy without his approval.
