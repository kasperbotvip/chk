# Telegram Bot on Render (aiogram v3)

## Setup
1. Create a bot and get BOT_TOKEN from @BotFather.
2. Set Render env vars:
   - BOT_TOKEN
   - ADMIN_IDS (e.g., `123456789,987654321`)
   - WEBHOOK_SECRET (random strong string)
   - APP_BASE_URL (your Render public URL like `https://telegram-bot-webhook.onrender.com`)
3. Deploy using render.yaml. Health check at `/health`.

## Webhook
- After first deploy, open your Render service, copy the public URL.
- Set `APP_BASE_URL` to that URL and redeploy (or set via Render dashboard).
- The app will call `setWebhook` on startup to `${APP_BASE_URL}/webhook` with secret token.

## Development
- Run locally:
  ```bash
  export BOT_TOKEN=... ADMIN_IDS=... WEBHOOK_SECRET=secret APP_BASE_URL=http://localhost:10000
  python -m app.main
