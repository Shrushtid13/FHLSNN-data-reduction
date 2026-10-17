import json
import logging
import secrets
from typing import Optional
import uuid
from fastapi import FastAPI, Header, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import redis
from supabase import create_client, Client

try:
    from .config import (
        REDIS_URL,
        INTERNAL_API_TOKEN,
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
        QUEUE_NAME,
    )
except (ImportError, ValueError):
    from config import (
        REDIS_URL,
        INTERNAL_API_TOKEN,
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
        QUEUE_NAME,
    )

logger = logging.getLogger("ml_service_api")

app = FastAPI(title="ML Service Internal API", version="1.0.0")

# Redis client
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL)
    return _redis_client


# Supabase client (service role)
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client


def verify_internal_token(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
) -> None:
    """
    Security: Constant-time comparison to prevent timing attacks.
    Ensures that only authorized internal services can call the ML service.
    """
    if not x_internal_token or not secrets.compare_digest(x_internal_token, INTERNAL_API_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "unauthorized", "detail": "Invalid or missing internal API token"},
        )


class JobRequest(BaseModel):
    experiment_id: str


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "fastapi-ml-service"}


@app.post("/jobs", status_code=status.HTTP_200_OK)
def enqueue_job(
    job: JobRequest,
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
    r: redis.Redis = Depends(get_redis_client),
):
    # Security: Verify token with constant-time equality
    verify_internal_token(x_internal_token)

    # Security: Validate experiment_id format (must be valid UUID)
    try:
        uuid.UUID(job.experiment_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "validation_error", "detail": "Invalid experiment_id UUID format"},
        )

    payload = json.dumps({"experiment_id": job.experiment_id})
    r.lpush(QUEUE_NAME, payload)

    return {"status": "queued", "experiment_id": job.experiment_id}


@app.get("/jobs/{id}")
def get_job_status(
    id: str,
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
    supabase: Client = Depends(get_supabase_client),
):
    # Security: Require internal token so arbitrary users cannot read any experiment via port 8000
    verify_internal_token(x_internal_token)

    # Security: Validate UUID
    try:
        uuid.UUID(id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "validation_error", "detail": "Invalid experiment ID UUID format"},
        )

    try:
        response = (
            supabase.table("experiments")
            .select("id, status, progress, metrics, error")
            .eq("id", id)
            .single()
            .execute()
        )
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": "not_found", "detail": f"Experiment {id} not found"},
            )
        row = response.data
        return {
            "experiment_id": row.get("id", id),
            "status": row.get("status"),
            "progress": row.get("progress", 0),
            "metrics": row.get("metrics"),
            "error": row.get("error"),
        }
    except HTTPException:
        raise
    except Exception as exc:
        # Security: Never leak database connection strings or raw exception messages to client
        logger.error(f"Database error fetching status for {id}: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "database_error", "detail": "An internal database error occurred"},
        )


# 501 Stubs for ML/LLM/profiling routes (protected by internal token)
@app.post("/profile", dependencies=[Depends(verify_internal_token)])
def profile_stub():
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content={"error": "not_implemented"})


@app.post("/recommend", dependencies=[Depends(verify_internal_token)])
def recommend_stub():
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content={"error": "not_implemented"})


@app.post("/explain", dependencies=[Depends(verify_internal_token)])
def explain_stub():
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content={"error": "not_implemented"})


@app.post("/agent/run", dependencies=[Depends(verify_internal_token)])
def agent_run_stub():
    return JSONResponse(status_code=status.HTTP_501_NOT_IMPLEMENTED, content={"error": "not_implemented"})
