import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from root or local directory
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "placeholder-internal-token")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://placeholder.supabase.co")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "placeholder-service-role-key")
QUEUE_NAME = "fhlsnn:jobs"

# In production, enforce that critical secrets are explicitly provided and not default placeholders
if os.getenv("ENV") == "production":
    if not INTERNAL_API_TOKEN or INTERNAL_API_TOKEN == "placeholder-internal-token":
        raise ValueError("FATAL SECURITY ERROR: INTERNAL_API_TOKEN must be securely set in production.")
    if not SUPABASE_SERVICE_ROLE_KEY or SUPABASE_SERVICE_ROLE_KEY == "placeholder-service-role-key":
        raise ValueError("FATAL SECURITY ERROR: SUPABASE_SERVICE_ROLE_KEY must be securely set in production.")

