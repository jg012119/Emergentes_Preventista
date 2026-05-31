import os
from dotenv import load_dotenv

load_dotenv()

# --- Supabase ---
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")

# --- JWT ---
JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

# --- Email ---
EMAIL_HOST: str = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER: str = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

import re

_PLACEHOLDER_MARKERS = ("your-project", "your-anon-key", "your-service-role-key")
_JWT_PATTERN = r"^[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$"

_USE_LOCAL_DB = (
    not SUPABASE_URL
    or not SUPABASE_KEY
    or any(marker in SUPABASE_URL for marker in _PLACEHOLDER_MARKERS)
    or any(marker in SUPABASE_KEY for marker in _PLACEHOLDER_MARKERS)
    or not re.match(_JWT_PATTERN, SUPABASE_KEY)
    or (SUPABASE_SERVICE_KEY and not re.match(_JWT_PATTERN, SUPABASE_SERVICE_KEY))
)

if _USE_LOCAL_DB:
    from app.local_db import get_local_client
    print("[WARNING] Supabase credentials not configured or invalid - using LOCAL SQLite database")
else:
    from supabase import create_client, Client


def get_supabase():
    """Return a Supabase client using the anon key (or local SQLite fallback)."""
    if _USE_LOCAL_DB:
        return get_local_client()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_admin():
    """Return a Supabase client using the service-role key (or local SQLite fallback)."""
    if _USE_LOCAL_DB:
        return get_local_client()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
