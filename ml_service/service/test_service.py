import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from ml_service.service.api import app, get_redis_client, get_supabase_client
from ml_service.service.config import INTERNAL_API_TOKEN, QUEUE_NAME
from ml_service.service.worker import run_experiment_job, start_worker


class FakeRedis:
    def __init__(self):
        self.lists = {}

    def lpush(self, key, value):
        if key not in self.lists:
            self.lists[key] = []
        self.lists[key].insert(0, value)
        return len(self.lists[key])

    def brpop(self, key, timeout=5):
        if key in self.lists and len(self.lists[key]) > 0:
            val = self.lists[key].pop()
            return (key, val)
        return None


class FakeSupabaseTable:
    def __init__(self, data_store):
        self.data_store = data_store
        self._current_id = None
        self._action = None
        self._update_fields = {}

    def select(self, columns):
        self._action = "select"
        return self

    def update(self, fields):
        self._action = "update"
        self._update_fields = fields
        return self

    def eq(self, col, val):
        if col == "id":
            self._current_id = val
        return self

    def single(self):
        return self

    def execute(self):
        mock_res = MagicMock()
        if self._action == "select":
            mock_res.data = self.data_store.get(self._current_id)
            return mock_res
        elif self._action == "update":
            if self._current_id not in self.data_store:
                self.data_store[self._current_id] = {"id": self._current_id}
            self.data_store[self._current_id].update(self._update_fields)
            mock_res.data = self.data_store[self._current_id]
            return mock_res
        return mock_res


class FakeSupabaseClient:
    def __init__(self):
        self.data_store = {}

    def table(self, name):
        return FakeSupabaseTable(self.data_store)


@pytest.fixture
def client():
    return TestClient(app)


def test_enqueue_job_token_check(client):
    fake_redis = FakeRedis()
    app.dependency_overrides[get_redis_client] = lambda: fake_redis
    valid_uuid = "00000000-0000-0000-0000-000000000001"

    # 1. No token -> 401
    resp_no_token = client.post("/jobs", json={"experiment_id": valid_uuid})
    assert resp_no_token.status_code == 401

    # 2. Invalid token -> 401
    resp_invalid = client.post(
        "/jobs",
        json={"experiment_id": valid_uuid},
        headers={"X-Internal-Token": "wrong-token"},
    )
    assert resp_invalid.status_code == 401

    # 3. Invalid UUID format -> 422
    resp_bad_uuid = client.post(
        "/jobs",
        json={"experiment_id": "not-a-uuid"},
        headers={"X-Internal-Token": INTERNAL_API_TOKEN},
    )
    assert resp_bad_uuid.status_code == 422

    # 4. Valid token & UUID -> 200 and enqueued to Redis
    resp_valid = client.post(
        "/jobs",
        json={"experiment_id": valid_uuid},
        headers={"X-Internal-Token": INTERNAL_API_TOKEN},
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json() == {"status": "queued", "experiment_id": valid_uuid}

    # Verify FakeRedis received payload
    assert len(fake_redis.lists.get(QUEUE_NAME, [])) == 1
    raw = fake_redis.lists[QUEUE_NAME][0]
    assert json.loads(raw) == {"experiment_id": valid_uuid}

    app.dependency_overrides.clear()


def test_stubs_return_501(client):
    endpoints = ["/profile", "/recommend", "/explain", "/agent/run"]
    for ep in endpoints:
        # Without internal token -> 401
        unauth = client.post(ep)
        assert unauth.status_code == 401

        # With internal token -> 501
        resp = client.post(ep, headers={"X-Internal-Token": INTERNAL_API_TOKEN})
        assert resp.status_code == 501
        assert resp.json() == {"error": "not_implemented"}


def test_get_job_status(client):
    fake_db = FakeSupabaseClient()
    valid_id = "00000000-0000-0000-0000-000000000099"
    fake_db.data_store[valid_id] = {
        "id": valid_id,
        "status": "running",
        "progress": 60,
        "metrics": None,
        "error": None,
    }
    app.dependency_overrides[get_supabase_client] = lambda: fake_db

    # 1. Unauthenticated -> 401
    unauth = client.get(f"/jobs/{valid_id}")
    assert unauth.status_code == 401

    # 2. Authenticated with invalid UUID -> 422
    bad_id = client.get("/jobs/not-uuid", headers={"X-Internal-Token": INTERNAL_API_TOKEN})
    assert bad_id.status_code == 422

    # 3. Authenticated with valid UUID -> 200
    resp = client.get(f"/jobs/{valid_id}", headers={"X-Internal-Token": INTERNAL_API_TOKEN})
    assert resp.status_code == 200
    data = resp.json()
    assert data["experiment_id"] == valid_id
    assert data["status"] == "running"
    assert data["progress"] == 60

    app.dependency_overrides.clear()


def test_worker_status_transitions_success():
    fake_db = FakeSupabaseClient()
    exp_id = "00000000-0000-0000-0000-000000000101"
    fake_db.data_store[exp_id] = {"id": exp_id, "status": "queued", "progress": 0}

    # Run experiment with 0 sleep for instant execution
    run_experiment_job(exp_id, client=fake_db, sleep_step_seconds=0)

    # After completion, status must be 'done', progress 100, metrics {"dummy": True}
    record = fake_db.data_store[exp_id]
    assert record["status"] == "done"
    assert record["progress"] == 100
    assert record["metrics"] == {"dummy": True}


def test_worker_status_transitions_failure():
    fake_db = FakeSupabaseClient()
    exp_id = "00000000-0000-0000-0000-000000000102"

    # Patch time.sleep to raise an exception simulating failure during job
    with patch("time.sleep", side_effect=RuntimeError("Simulated computational failure at C:\\Users\\secret\\path")):
        run_experiment_job(exp_id, client=fake_db, sleep_step_seconds=0.01)

    record = fake_db.data_store[exp_id]
    assert record["status"] == "failed"
    # Verify file system paths were sanitized
    assert "C:\\Users" not in record["error"]
    assert "[path_redacted]" in record["error"]


def test_worker_brpop_loop_with_fake_redis():
    fake_redis = FakeRedis()
    fake_db = FakeSupabaseClient()
    exp_id = "00000000-0000-0000-0000-000000000103"
    fake_db.data_store[exp_id] = {"id": exp_id, "status": "queued", "progress": 0}

    # Push job to fake redis
    fake_redis.lpush(QUEUE_NAME, json.dumps({"experiment_id": exp_id}))

    with patch("ml_service.service.worker.get_supabase_client", return_value=fake_db):
        start_worker(redis_client=fake_redis, timeout=1, max_jobs=1)

    record = fake_db.data_store[exp_id]
    assert record["status"] == "done"
    assert record["progress"] == 100
