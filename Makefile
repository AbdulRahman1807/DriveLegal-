.PHONY: dev up down restart logs migrate upgrade seed test clean format lint

dev:
	source venv/bin/activate && uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

migrate:
	source venv/bin/activate && alembic revision --autogenerate -m "auto_migration"

upgrade:
	source venv/bin/activate && alembic upgrade head

seed:
	source venv/bin/activate && python -m backend.seeds.run_seeds

test:
	source venv/bin/activate && pytest -v

format:
	source venv/bin/activate && black backend/
	source venv/bin/activate && isort backend/

lint:
	source venv/bin/activate && flake8 backend/
	source venv/bin/activate && mypy backend/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
