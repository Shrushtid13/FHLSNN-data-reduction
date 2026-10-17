import json
import logging
import re
import time
from typing import Any, Dict, Optional
import uuid
import redis
from supabase import create_client, Client

try:
    from .config import (
        REDIS_URL,
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
        QUEUE_NAME,
    )
except (ImportError, ValueError):
    from config import (
        REDIS_URL,
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
        QUEUE_NAME,
    )

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("worker")

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return _supabase_client


def sanitize_error_message(exc: Exception) -> str:
    """
    Security: Sanitize exception strings before persisting to database.
    Strips internal file system paths, credentials, and bounds message length.
    """
    msg = str(exc)
    # Strip Windows or Unix file paths
    msg = re.sub(r'[A-Za-z]:\\[^\s"\',]+', '[path_redacted]', msg)
    msg = re.sub(r'/[^\s"\',]+', '[path_redacted]', msg)
    # Strip potential credentials or connection strings
    msg = re.sub(r'(postgres|redis|http|https)://[^\s@]+@[^\s/]+', r'\1://[credentials_redacted]', msg)
    # Bound to 500 characters
    return msg[:500] if len(msg) > 500 else msg


def update_experiment_in_db(
    experiment_id: str,
    fields: Dict[str, Any],
    client: Optional[Client] = None,
) -> None:
    """Updates an experiment record in Supabase using the service role client."""
    db = client or get_supabase_client()
    db.table("experiments").update(fields).eq("id", experiment_id).execute()


def run_experiment_job(
    experiment_id: str,
    client: Optional[Client] = None,
    sleep_step_seconds: float = 0.5,
) -> None:
    """
    Executes an experiment job.
    For the initial skeleton, runs a dummy job simulating execution over 5 seconds (10 steps).
    This function is pluggable so the real FHLSNN runner can replace it later.
    """
    logger.info(f"Starting job for experiment: {experiment_id}")
    try:
        # Step 1: Set status to 'running'
        update_experiment_in_db(experiment_id, {"status": "running", "progress": 0}, client=client)

        # Step 2: Sleep in 10 steps updating progress 10..100
        for step in range(1, 11):
            if sleep_step_seconds > 0:
                time.sleep(sleep_step_seconds)
            progress = step * 10
            update_experiment_in_db(experiment_id, {"progress": progress}, client=client)
            logger.info(f"Experiment {experiment_id} progress: {progress}%")

        # Step 3: Set status to 'done' with dummy metrics
        update_experiment_in_db(
            experiment_id,
            {
                "status": "done",
                "progress": 100,
                "metrics": {"dummy": True},
            },
            client=client,
        )
        logger.info(f"Experiment {experiment_id} completed successfully (status: done).")

    except Exception as exc:
        logger.error(f"Experiment {experiment_id} failed with error: {exc}", exc_info=True)
        try:
            # Security: Sanitize error text to prevent path or credential disclosure
            safe_error = sanitize_error_message(exc)
            update_experiment_in_db(
                experiment_id,
                {
                    "status": "failed",
                    "error": safe_error,
                },
                client=client,
            )
        except Exception as update_err:
            logger.error(f"Failed to record failure status in db: {update_err}")


def start_worker(
    redis_client: Optional[redis.Redis] = None,
    supabase_client: Optional[Client] = None,
    timeout: int = 5,
    max_jobs: Optional[int] = None,
) -> None:
    """
    Worker main loop popping jobs from the Redis queue via BRPOP.
    """
    r = redis_client or redis.from_url(REDIS_URL)
    db = supabase_client or get_supabase_client()
    logger.info(f"Worker listening on queue: {QUEUE_NAME} (timeout: {timeout}s)...")
    processed_count = 0

    while True:
        try:
            item = r.brpop(QUEUE_NAME, timeout=timeout)
            if item is None:
                continue

            _, raw_payload = item
            if isinstance(raw_payload, bytes):
                raw_payload = raw_payload.decode("utf-8")

            payload = json.loads(raw_payload)
            experiment_id = payload.get("experiment_id")

            if not experiment_id:
                logger.warning(f"Received malformed payload missing experiment_id: {raw_payload}")
                continue

            # Security: Validate experiment_id is a valid UUID
            try:
                uuid.UUID(str(experiment_id))
            except (ValueError, TypeError):
                logger.warning(f"Received invalid UUID in payload: {experiment_id}")
                continue

            run_experiment_job(experiment_id, client=db)
            processed_count += 1

            if max_jobs is not None and processed_count >= max_jobs:
                logger.info(f"Processed {processed_count} jobs, exiting as requested.")
                break

        except KeyboardInterrupt:
            logger.info("Worker interrupted by user, exiting...")
            break
        except Exception as exc:
            logger.error(f"Error in worker loop: {exc}", exc_info=True)
            time.sleep(1)


if __name__ == "__main__":
    start_worker()
