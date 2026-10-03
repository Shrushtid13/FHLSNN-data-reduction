.PHONY: setup test test-core test-reducers test-agents dev-api dev-worker benchmark

setup:
	pip install -r requirements.txt

test:
	pytest tests/

test-core:
	pytest tests/test_fhlsnn.py

benchmark:
	python -m ml_service.benchmark.runner

dev-api:
	uvicorn ml_service.main:app --reload --port 8000

dev-worker:
	rq worker -w ml_service.worker
