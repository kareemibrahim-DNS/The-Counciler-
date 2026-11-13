# Slack setup (one time, Slack admin + Partnerships)

1. **Create the app:** api.slack.com/apps → *Create New App* → *From an app manifest* → paste the manifest below → pick the Foodics workspace.
2. **Install** it to the workspace (Slack admin approval). Copy the **Bot User OAuth Token** (`xoxb-...`) and, from *Basic Information*, the **Signing Secret**.
3. **Deploy the Worker:**
   ```bash
   npm ci
   npx wrangler secret put SLACK_BOT_TOKEN
   npx wrangler secret put SLACK_SIGNING_SECRET
   npx wrangler secret put ANTHROPIC_API_KEY
   npm run deploy
   ```
   Note the Worker URL, e.g. `https://reselling-copilot.<account>.workers.dev`.
4. In the app's *Event Subscriptions*, set the Request URL to `<worker-url>/slack/events`. Slack verifies it automatically.
5. **Invite the bot** to the channels where people should use it: `/invite @Reselling Copilot`.
6. **Partner channels:** check that every channel with partner staff is listed in `data/channels.json`. Unlisted shared channels get no pricing at all.

## Manifest

```yaml
display_information:
  name: Reselling Copilot
  description: Marketplace partner line items and quote structure. No cost data.
features:
  bot_user:
    display_name: Reselling Copilot
    always_online: true
  app_home:
    messages_tab_enabled: true
    messages_tab_read_only_enabled: false
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - chat:write
      - channels:read
      - groups:read
      - im:read
      - im:history
      - channels:history
      - groups:history
settings:
  event_subscriptions:
    request_url: https://REPLACE-WITH-WORKER-URL/slack/events
    bot_events:
      - app_mention
      - message.im
  org_deploy_enabled: false
  socket_mode_enabled: false
```

`channels:history` / `groups:history` are only used to read the thread the bot was mentioned in, so it can follow the conversation.
