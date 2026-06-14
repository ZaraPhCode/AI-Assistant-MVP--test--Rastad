import os
from dotenv import load_dotenv

load_dotenv()

# Default to PostgreSQL via env; fallback to SQLite if not set (for quick local testing)
DATABASE_URL = os.getenv("DATABASE_URL")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")