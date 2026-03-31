import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        # SQLAlchemy requires "postgresql://" for async/sync drivers
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif "postgresql://" in DATABASE_URL and "postgresql+asyncpg://" not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Remove ?pgbouncer=true if present as it causes issues with asyncpg connect()
    if "?pgbouncer=true" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("?pgbouncer=true", "")
    elif "&pgbouncer=true" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace("&pgbouncer=true", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Validate required variables
if not DATABASE_URL:
    if ENVIRONMENT == "production":
        raise ValueError("DATABASE_URL environment variable is required in production")
    # For local/dev mode if DATABASE_URL is missing, use fallback sqlite and warn
    DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/db" # Default local fallback
    logger.warning("DATABASE_URL not set; using placeholder URL for development")

# Warn about missing optional API key in development
if not ANTHROPIC_API_KEY:
    if ENVIRONMENT == "production":
        raise ValueError("ANTHROPIC_API_KEY is required in production")
    else:
        logger.warning("ANTHROPIC_API_KEY not set. Using fallback responses for chat.")

logger.info(f"JournoMind backend initialized in {ENVIRONMENT} mode")

