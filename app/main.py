import logging
from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import httpx

from app.database import engine, Base
from app.routers import messages, users
from app.schemas import MessageRequest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Rastad AI Assistant MVP")

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

# ----------- FRONTEND ROUTES -----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/users-page", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse("users.html", {"request": request})