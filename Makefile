.PHONY: up down logs shell lint install dev

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec db psql -U privmail -d privmail

install:
	cd backend && pip3 install -r requirements.txt

dev:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

lint:
	cd backend && python3 -m ruff check . && python3 -m ruff format --check .
