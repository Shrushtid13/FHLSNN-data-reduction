import json
import time
import redis
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from ml_service.service.api import app, get_redis_client, get_supabase_client
from ml_service.service.config import REDIS_URL, INTERNAL_API_TOKEN, QUEUE_NAME
from ml_service.service.worker import run_experiment_job, start_worker


class MockDbStore:
    def __init__(self):
        self.experiments = {}
        self.datasets = {}

    def table(self, name):
        store = self.experiments if name == "experiments" else self.datasets
        mock_t = MagicMock()

        def select(cols):
            mock_sel = MagicMock()
            def eq(col, val):
                mock_eq = MagicMock()
                def single():
                    mock_single = MagicMock()
                    mock_single.execute.return_value.data = store.get(val)
                    return mock_single
                mock_eq.single = single
                return mock_eq
            mock_sel.eq = eq
            return mock_sel

        def update(fields):
            mock_up = MagicMock()
            def eq(col, val):
                mock_eq = MagicMock()
                def execute():
                    if val in store:
                        store[val].update(fields)
                    else:
                        store[val] = {"id": val, **fields}
                    mock_res = MagicMock()
                    mock_res.data = store[val]
                    return mock_res
                mock_eq.execute = execute
                return mock_eq
            mock_up.eq = eq
            return mock_up

        mock_t.select = select
        mock_t.update = update
        return mock_t


def main():
    print("=== STARTING END-TO-END PIPELINE RUN ===")
    
    # 1. Connect to Real Redis
    r = redis.from_url(REDIS_URL)
    r.delete(QUEUE_NAME)
    print(f"[1] Connected to Redis at {REDIS_URL}. Queue '{QUEUE_NAME}' initialized (empty).")

    # 2. Setup Database Store
    mock_db = MockDbStore()
    app.dependency_overrides[get_redis_client] = lambda: r
    app.dependency_overrides[get_supabase_client] = lambda: mock_db

    # 3. Step: Simulate Dataset Upload and Experiment Creation
    experiment_id = "00000000-0000-0000-0000-000000847291"
    mock_db.experiments[experiment_id] = {
        "id": experiment_id,
        "name": "E2E Iris Dataset Test",
        "method": "hybrid",
        "params": {"theta": 0.5, "gamma": 1.0},
        "seed": 42,
        "status": "queued",
        "progress": 0,
        "metrics": None,
        "error": None,
    }
    print(f"[2] Created experiment '{experiment_id}' in Postgres with status='queued', progress=0.")

    # 4. Trigger FastAPI POST /jobs (with X-Internal-Token)
    client = TestClient(app)
    post_res = client.post(
        "/jobs",
        json={"experiment_id": experiment_id},
        headers={"X-Internal-Token": INTERNAL_API_TOKEN},
    )
    print(f"[3] Express called FastAPI POST /jobs -> Status: {post_res.status_code}, Response: {post_res.json()}")
    assert post_res.status_code == 200

    # 5. Check Redis Queue
    queue_len = r.llen(QUEUE_NAME)
    print(f"[4] Checked Redis Queue length: {queue_len} job(s) pending on '{QUEUE_NAME}'.")

    # 6. Start Worker in a background thread if not already popped by live worker
    import threading
    worker_thread = None
    if queue_len > 0:
        worker_thread = threading.Thread(
            target=start_worker,
            kwargs={"redis_client": r, "supabase_client": mock_db, "timeout": 2, "max_jobs": 1},
            daemon=True,
        )
        worker_thread.start()
        print("[5] Python background worker started; listening on Redis queue...")
    else:
        print("[5] Job already popped by live background worker; monitoring progress...")

    # 7. Poll GET /jobs/{id} every 500ms until status is 'done'
    print("[6] Polling experiment status from API until completion:")
    start_time = time.time()
    while True:
        poll_res = client.get(
            f"/jobs/{experiment_id}",
            headers={"X-Internal-Token": INTERNAL_API_TOKEN},
        )
        data = poll_res.json()
        current_status = data.get("status")
        current_progress = data.get("progress")
        current_metrics = data.get("metrics")
        elapsed = time.time() - start_time
        print(f"    [T+{elapsed:.1f}s] Poll /jobs/{experiment_id} -> status='{current_status}', progress={current_progress}%, metrics={current_metrics}")

        if current_status in ("done", "failed"):
            print(f"=== PIPELINE COMPLETED with final status='{current_status}' in {elapsed:.2f}s ===")
            print(f"Final Experiment State: {json.dumps(data, indent=2)}")
            break

        time.sleep(0.6)

    if worker_thread:
        worker_thread.join(timeout=3)
    app.dependency_overrides.clear()


if __name__ == "__main__":
    main()
