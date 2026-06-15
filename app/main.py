import logging
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

from app.database import engine, Base
from app.routers import messages, users
from app.schemas import MessageRequest

import os
from contextlib import asynccontextmanager
from app.telegram import telegram_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Set Telegram webhook
    try:
        if os.getenv("SET_TELEGRAM_WEBHOOK", "false").lower() == "true":
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            base_url = os.getenv('BASE_URL', 'http://localhost:8000')
            
            if bot_token:
                webhook_url = f"{base_url}/webhook/telegram"
                response = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/setWebhook",
                    json={"url": webhook_url}
                )
                response.raise_for_status()
                logger.info(f"Telegram webhook set to: {webhook_url}")
                logger.info(f"Webhook response: {response.json()}")
            else:
                logger.warning("TELEGRAM_BOT_TOKEN not set. Telegram bot disabled.")
    except Exception as e:
        logger.error(f"Failed to set Telegram webhook: {str(e)}")
    
    yield
    
    # Shutdown: Clear webhook
    try:
        if os.getenv("SET_TELEGRAM_WEBHOOK", "false").lower() == "true":
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            if bot_token:
                requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")
                logger.info("Telegram webhook removed")
    except Exception as e:
        logger.error(f"Failed to remove webhook: {str(e)}")

app = FastAPI(title="Rastad AI Assistant MVP", lifespan=lifespan)

# Templates
templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple rate limiter
request_counts = {}

@app.middleware("http")
async def simple_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api"):
        client_ip = request.client.host
        if client_ip in request_counts:
            request_counts[client_ip] += 1
            if request_counts[client_ip] > 100:
                return JSONResponse(status_code=429, content={"detail": "Too many requests"})
        else:
            request_counts[client_ip] = 1
    response = await call_next(request)
    return response

# Include API routers under /api prefix
app.include_router(messages.router, prefix="/api", tags=["Messages"])
app.include_router(users.router, prefix="/api", tags=["Users"])

@app.get("/api/")
def api_root():
    return {"message": "Rastad AI Assistant API is running"}

# Telegram webhook endpoint
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram"""
    try:
        update = await request.json()
        logger.info(f"Received Telegram update: {update}")
        
        # Handle message
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "").strip()
            
            if text:
                # Handle /start command
                if text == "/start":
                    telegram_bot.send_message(
                        chat_id,
                        "🌟 *به دستیار هوشمند راستاد خوش آمدید!*\n\n"
                        "من می‌توانم به سوالات شما درباره خدمات راستاد پاسخ دهم:\n"
                        "• خدمات VIP\n"
                        "• ثبت‌نام در صرافی\n"
                        "• همکاری KOL\n"
                        "• پشتیبانی و مشکلات\n"
                        "• اطلاعات عمومی\n\n"
                    )
                    telegram_bot.show_main_menu(chat_id)
                else:
                    # Process other messages
                    telegram_bot.handle_message(chat_id, text)
            
            return {"status": "ok"}
        
        # Handle callback queries if needed
        if "callback_query" in update:
            # Not used in this MVP, but available for future
            return {"status": "ignored"}
        
        logger.warning("Update doesn't contain a message or callback_query")
        return {"status": "ignored"}
        
    except Exception as e:
        logger.error(f"Error processing Telegram webhook: {str(e)}", exc_info=True)
        return {"status": "error"}
# ----------- FRONTEND ROUTES -----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/users-page", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})