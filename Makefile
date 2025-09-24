.PHONY: install test run lint format clean

install:
	pip install -r requirements.txt

test:
	pytest

run:
	python -m src.mi_app_completa_backend.infrastructure.web.fastapi.main

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

dev: install
	uvicorn src.mi_app_completa_backend.infrastructure.web.fastapi.main:app --reload --host 0.0.0.0 --port 8000