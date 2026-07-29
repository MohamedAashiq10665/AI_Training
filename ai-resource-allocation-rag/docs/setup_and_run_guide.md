# Full Setup and Run Guide

## 1. Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop
- Ollama installed locally (for non-Docker Ollama usage)

## 2. Clone and Prepare

```bash
cd AI_Training/ai-resource-allocation-rag
cp .env.example .env
```

Update `.env` values for production security:

- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `OLLAMA_MODEL`

## 3. Local Run (Without Docker)

### Backend

```bash
python -m pip install -r requirements.txt
python data/generate_synthetic_data.py
python -m backend.database.init_db
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 4. Docker Run

```bash
docker compose up --build
```

Service URLs:

- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Ollama: http://localhost:11434

## 5. Default Users

Seeded users are created automatically for the core roles:

- `admin`
- `manager`
- `viewer`

Use `POST /auth/login` with your configured credentials to get a Bearer token.

## 6. Auth Flow Example

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<your-username>","password":"<your-password>"}'
```

Then call protected APIs using:

```text
Authorization: Bearer <token>
```

Role behavior in current UI:

- `admin` and `manager`: full recommendation and project allocation actions.
- `viewer`: read-only workspace (cannot assign, unassign, or trigger recommendation generation actions).

Core operational endpoints now include:

- `GET /project-teams`
- `GET /projects`
- `GET /projects/{project_id}/details`
- `POST /projects/{project_id}/assign`
- `POST /projects/{project_id}/unassign`
- `POST /projects/{project_id}/ai-recommend-chat`

Chat scope guardrails:

- `/chat` and project AI chat support staffing/allocation queries only.
- Unrelated prompts return HTTP 400 with supported-scope detail.

Recommendation input guardrails:

- `/recommend` expects skill names, not free-form natural-language prompts.
- The dashboard validates skill input before sending the request.
- The backend also rejects empty or unrelated non-skill recommendation input with HTTP 400.

## 7. Run Benchmark Automatically

```bash
python analytics/model_benchmark_runner.py
```

Outputs:

- `data/model_benchmark_results.csv`
- `data/model_benchmark_results.json`
- `docs/model_benchmark_results.md`

## 8. Test Execution

```bash
pytest
```

Coverage command:

```bash
pytest --cov=backend --cov=rag --cov=recommendation_engine --cov-report=term
```

## 9. Troubleshooting

- If DB connection fails, verify `DATABASE_URL` and PostgreSQL service status.
- If `/chat` fails, ensure Ollama is running and selected model is pulled.
- If benchmark fails, run:
  - `ollama pull llama3:8b`
  - `ollama pull phi3:mini`
