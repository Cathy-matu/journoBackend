import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate required variables
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Warn about missing optional API key in development
if not ANTHROPIC_API_KEY:
    if ENVIRONMENT == "production":
        raise ValueError("ANTHROPIC_API_KEY is required in production")
    else:
        logger.warning("ANTHROPIC_API_KEY not set. Using fallback responses for chat.")

logger.info(f"JournoMind backend initialized in {ENVIRONMENT} mode")

