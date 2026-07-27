# AI-Powered Resource Allocation & Bench Management with RAG

This project is a production-style MVP that recommends best-fit employees for project opportunities using Retrieval Augmented Generation (RAG), weighted scoring, and workforce analytics.

## Core Capabilities

- Synthetic workforce and project data generation
- RAG-based employee retrieval with FAISS and local embeddings
- Explainable staffing recommendations and skill-gap analysis
- Bench and utilization analytics
- JWT authentication and role-based access control (RBAC)
- Role-aware frontend UX (viewer read-only, manager/admin operational actions)
- PostgreSQL persistence for runtime APIs
- FastAPI backend APIs
- React dashboard with Material UI and Recharts
- Dashboard AI recommendation chat with staffing-only prompt validation
- Employees/Projects operational workspace with dedicated project details view
- Project allocation lifecycle: assign and unassign members
- AI-driven fit candidates in project details
- Cross-project AI recommendation chat
- Chat guardrails that reject non-staffing questions with explicit error messages
- Frontend chat validation for empty, too-short, and out-of-scope dashboard prompts
- Local LLM chat assistant through Ollama
- Model comparison report (Llama 3 8B vs Phi-3 Mini)
- Automated model benchmark runner for Ollama models

## Tech Stack

- Backend: FastAPI, Python, SQLAlchemy, PostgreSQL
- RAG: LangChain, FAISS, sentence-transformers embeddings
- LLM: Ollama (Llama 3 8B / Phi-3 Mini)
- Frontend: React, Material UI, Recharts
- Testing: Pytest
- Deployment: Docker Compose

## Quick Start

1. Copy `.env.example` to `.env`.
2. Pull local models (recommended):

```bash
ollama pull llama3:8b
ollama pull phi3:mini
```

3. Start services:

```bash
docker compose up --build
```

4. Generate data (for non-Docker local runs):

```bash
python data/generate_synthetic_data.py
```

5. Build FAISS index:

```bash
python rag/pipelines/employee_rag_pipeline.py
```

6. API docs:

- http://localhost:8000/docs

7. Frontend:

- http://localhost:5173

## API Endpoints

Authentication:

- `POST /auth/login`
- `GET /auth/me`

- `POST /recommend`
- `POST /chat`
- `GET /employees`
- `GET /project-teams`
- `GET /projects`
- `GET /projects/{project_id}/details`
- `POST /projects/{project_id}/assign`
- `POST /projects/{project_id}/unassign`
- `POST /projects/{project_id}/ai-recommend-chat`
- `GET /analytics`
- `GET /bench`
- `GET /utilization`

Detailed API examples are in `docs/api_documentation.md`.

## Testing

```bash
pytest
pytest --cov=backend --cov=rag --cov=recommendation_engine --cov-report=term
```

## Benchmark Runner

```bash
python analytics/model_benchmark_runner.py
```

Benchmark outputs:

- `data/model_benchmark_results.csv`
- `data/model_benchmark_results.json`
- `docs/model_benchmark_results.md`

## Documentation

- Architecture: `docs/architecture.md`
- Prompt engineering: `docs/prompt_engineering_report.md`
- Model comparison: `docs/model_comparison_report.md`
- Testing strategy: `docs/testing_strategy.md`
- Limitations and roadmap: `docs/limitations_future.md`
- Deployment: `deployment/deploy_guide.md`
- Full setup guide: `docs/setup_and_run_guide.md`
- Final artifacts list: `docs/final_artifacts.md`