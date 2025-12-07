import os
from aiohttp import web
from app.web import init_app
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    app = init_app()
    web.run_app(app, host=settings.host, port=settings.port)
