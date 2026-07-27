# Deployment Guide

## Local Deployment

1. Copy `.env.example` to `.env`.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Generate datasets: `python data/generate_synthetic_data.py`.
4. Initialize and seed PostgreSQL schema: `python -m backend.database.init_db`.
5. Start API: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`.
6. Start frontend: from `frontend`, run `npm install` then `npm run dev`.

## Docker Deployment

1. Ensure `.env` exists and has valid values.
2. Start stack:

```bash
docker compose up --build
```

What Docker startup now does:

- Generates synthetic datasets
- Starts backend connected to PostgreSQL
- Initializes and seeds DB on API startup
- Exposes frontend, backend, PostgreSQL, and Ollama

## Ollama Model Setup

Run on host or inside Ollama container:

```bash
ollama pull llama3:8b
ollama pull phi3:mini
```

Set `OLLAMA_MODEL` in `.env` to switch between models.

## Authentication

Seeded users:

- `admin / admin123`
- `manager / manager123`
- `viewer / viewer123`

Get token:

```bash
curl -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"username":"manager","password":"manager123"}'
```

## Automated Benchmark Run

```bash
python analytics/model_benchmark_runner.py
```

Generated outputs:

- `data/model_benchmark_results.csv`
- `data/model_benchmark_results.json`
- `docs/model_benchmark_results.md`

## Full Documentation

- Setup and run manual: `docs/setup_and_run_guide.md`
- Final artifact inventory: `docs/final_artifacts.md`
