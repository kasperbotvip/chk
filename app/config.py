import os
from dataclasses import dataclass

@dataclass
class Settings:
    bot_token: str
    admin_ids: list[int]
    webhook_secret: str
    app_base_url: str
    port: int
    host: str

def get_settings() -> Settings:
    # Embedded defaults (used only if env vars are missing)
    DEFAULT_BOT_TOKEN = "5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg"
    DEFAULT_ADMIN_IDS = [988757303]

    token = os.getenv("BOT_TOKEN", DEFAULT_BOT_TOKEN)
    admin_raw = os.getenv("ADMIN_IDS", ",".join(str(i) for i in DEFAULT_ADMIN_IDS))
    admin_ids = [int(p.strip()) for p in admin_raw.split(",") if p.strip().isdigit()]

    secret = os.getenv("WEBHOOK_SECRET", "secret123")
    base_url = os.getenv("APP_BASE_URL", "https://chk-aq5u.onrender.com")
    port = int(os.getenv("PORT", "10000"))
    host = os.getenv("HOST", "0.0.0.0")

    return Settings(
        bot_token=token,
        admin_ids=admin_ids,
        webhook_secret=secret,
        app_base_url=base_url,
        port=port,
        host=host
    )
