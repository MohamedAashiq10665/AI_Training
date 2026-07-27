# Testing Strategy

## Test Types

- Unit Tests: scoring, security utilities, and benchmark runner artifact generation.
- Integration Tests: FastAPI endpoint behavior, login flow, RBAC permissions, project details, assign/unassign flows, and constrained AI chat behavior.
- Performance Tests: retrieval latency threshold.

## Coverage Goal

- Target: 80%+ on backend and RAG modules.
- Command: `pytest --cov=backend --cov=rag --cov=recommendation_engine tests/`

## Retrieval Quality Validation

- Check if top results contain requested skills.
- Measure precision@k on sampled staffing queries.

## Security Validation

- Verify password hashing and token decoding logic.
- Verify `viewer` access restrictions on manager-only endpoints.

## Project Operations Validation

- Validate `GET /projects` returns allocation-aware project list.
- Validate `GET /projects/{project_id}/details` returns allocated members and AI-driven fit candidates.
- Validate assign action updates project allocations and employee utilization.
- Validate unassign action recomputes utilization from remaining allocations.

## Chat Guardrail Validation

- Validate staffing-related prompts are accepted on `/chat` and `/projects/{project_id}/ai-recommend-chat`.
- Validate unrelated prompts return HTTP 400 with explicit supported-topic error details.

## Dashboard Recommendation Validation

- Validate dashboard UI blocks recommendation requests when no required skills are provided.
- Validate dashboard UI blocks recommendation requests when any entered skill is shorter than 2 characters.
- Validate dashboard and `/recommend` both reject natural-language or unrelated non-skill prompts.
