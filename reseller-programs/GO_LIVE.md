# Go live (you run deploy)

Deploy prints a one-time alias token. Run these on your machine so the token stays out of chat.

Cloud Agent dry-run on 2026-11-13 UTC returned `unauthenticated` (no `CURSOR_API_KEY` / service account). Catalog + validate already pass — only login/deploy is left for you.

## 1. Login

```bash
cd reseller-programs
npx --yes "@grok/agent-sdk@0.6.0" login
```

## 2. Validate

```bash
npm run feed
npm run check
npx --yes "@grok/agent-sdk@0.6.0" validate --dir .
```

## 3. Dry-run then deploy

```bash
npx --yes "@grok/agent-sdk@0.6.0" deploy --dir . --dry-run --json
npx --yes "@grok/agent-sdk@0.6.0" deploy --dir .
```

Save the alias token in a password manager.

## 4. Smoke the hosted agent

```bash
npx --yes "@grok/agent-sdk@0.6.0" session create --slug reseller-programs --message "Which partners work in SA?" --wait
npx --yes "@grok/agent-sdk@0.6.0" session create --slug reseller-programs --message "What is the Grubtech - gOnline License [Annual] price in SA?" --wait
npx --yes "@grok/agent-sdk@0.6.0" session create --slug reseller-programs --message "Write a poem about coffee." --wait
```

Manage at https://cursor.com/dashboard/deployed-agents

## Local playground (before deploy)

```bash
npx --yes "@grok/agent-sdk@0.6.0" dev
```

Playground: http://127.0.0.1:3000/reseller-programs/playground

Try: partners in `SA`, Grubtech quote structure, Grubtech gOnline Annual price in `SA`, off-topic refuse.

Tool smoke evidence: [`docs/SMOKE-EVIDENCE.md`](docs/SMOKE-EVIDENCE.md)
