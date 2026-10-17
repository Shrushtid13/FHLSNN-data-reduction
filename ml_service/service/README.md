# ML Service: FastAPI & Worker

This directory contains the Python FastAPI internal service and the background worker handling asynchronous experiment execution on Windows via Redis LPUSH / BRPOP.

## Prerequisites

Ensure Redis is running (e.g., via Docker):
```powershell
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Install requirements:
```powershell
pip install -r requirements.txt
```

---

## 1. Start FastAPI Service

Start the FastAPI application on port 8000 using Uvicorn:

```powershell
# From the repository root:
python -m uvicorn ml_service.service.api:app --host 0.0.0.0 --port 8000 --reload

# Or from inside ml_service/service/:
cd ml_service\service
python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI schema: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 2. Start Background Worker

In a separate PowerShell window, start the worker process listening on `fhlsnn:jobs`:

```powershell
# From the repository root:
python -m ml_service.service.worker

# Or from inside ml_service/service/:
cd ml_service\service
python worker.py
```

The worker continuously polls Redis with `BRPOP` (5-second timeout), receives job payloads, simulates or runs experiment execution, and updates Postgres progress (10..100) and final metrics.

---

## 3. Run Tests

To run the automated tests for FastAPI endpoints and the worker:

```powershell
pytest ml_service/service/test_service.py -v
```
