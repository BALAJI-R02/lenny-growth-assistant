.PHONY: ingest test build up down logs clean

# Start all services
up:
	docker compose up --build -d

# Stop all services
down:
	docker compose down

# View logs
logs:
	docker compose logs -f

# Run ingest script (clones repo, chunks, inserts into DB)
ingest:
	docker compose exec backend python -m app.ingest

# Run tests (LLM mocked, offline)
test:
	docker compose exec backend pytest tests/ -v $(ARGS)

# Run tests locally (requires .venv)
test-local:
	cd backend && python -m pytest tests/ -v $(ARGS)

# Clean everything including volumes
clean:
	docker compose down -v
	docker system prune -f

# Show backend logs only
backend-logs:
	docker compose logs -f backend

# Open a shell in backend container
shell:
	docker compose exec backend bash

# Quick health check
health:
	curl -s http://localhost:8000/health | python -m json.tool
