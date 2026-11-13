# رسائل Cursor في Slack (بالترتيب)

ابعت كل رسالة لـ @Cursor في Slack. متبعتش اللي بعدها غير لما تراجع الـ PR بتاع اللي قبلها وتعمله merge.
اكتب اسم الـ repo في الرسالة لو Cursor سألك (مثلاً: repo=kareemibrahim-DNS/The-Counciler-).

---

**1. الهيكل والشاشات**
```
@Cursor Read SPEC.md fully. Do build step 1 only: scaffold the monorepo (apps/web, apps/worker, packages/shared) and build the PWA shell with the 3 tabs and static screens matching design/Main.dc.html and design/Usage.dc.html exactly (RTL Arabic, colors and fonts from SPEC section 7). Open a PR, do not merge.
```

**2. السيرفر والدخول**
```
@Cursor Following SPEC.md, do build step 2: Worker skeleton with Hono, D1 schema and migrations, passcode login with HttpOnly session in KV, .env.example. Open a PR, do not merge.
```

**3. أول رد حقيقي**
```
@Cursor Following SPEC.md section 3, do build step 3: provider clients for Claude, OpenAI, DeepSeek, xAI (model IDs from env vars), the judge, and Best-fit mode working end to end from the Council screen. Open a PR, do not merge.
```

**4. الكل يرد والسجل**
```
@Cursor Following SPEC.md, do build step 4: Everyone mode with parallel calls and timeouts, judge merge, and run history saved in D1 and shown in the app. Open a PR, do not merge.
```

**5. Slack**
```
@Cursor Following SPEC.md section 4 exactly, do build step 5: /slack/events endpoint with signature check, 3-second ack, retry dedupe, allow-list, thread reply with chat.update. Add a SLACK_SETUP.md with the manifest and the steps for me to create the Slack app. Open a PR, do not merge.
```

**6. الرصيد**
```
@Cursor Following SPEC.md section 5, do build step 6: usage ledger, price table, budgets in Settings, DeepSeek balance reconciliation, forecast, and the Usage screen with live data and the low-balance banner. Open a PR, do not merge.
```

**7. النشر**
```
@Cursor Do build step 7 from SPEC.md: deployment config for Cloudflare Pages and the Worker, and a DEPLOY.md with every command I need to run (wrangler secrets, D1 create, deploy). Do not deploy anything yourself. Open a PR.
```
