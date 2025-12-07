import os
from dataclasses import dataclass

@dataclass
class Settings:
    bot_token: str
    admin_ids: list[int]
    webhook_secret: str
    port: int
    host: str

def get_settings() -> Settings:
    token = os.getenv("5788330295:AAHhDVCjGt6g2vBrCuyAKK5Zjj3o73s7yTg", "")
    if not token:
        raise RuntimeError("BOT_TOKEN is required")

    admin_raw = os.getenv("ADMIN_IDS", "")
    admin_ids = []
    for part in admin_raw.split(","):
        part = part.strip()
        if part.isdigit():
            admin_ids.append(int(part))

    secret = os.getenv("WEBHOOK_SECRET", "")
    if not secret:
        raise RuntimeError("WEBHOOK_SECRET is required")

    port = int(os.getenv("PORT", "10000"))  # Render يمرر PORT تلقائياً للخدمة
    host = os.getenv("HOST", "0.0.0.0")
    return Settings(token, admin_ids, secret, port, host)
