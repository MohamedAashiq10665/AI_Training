# Testing Strategy

## Test Types

- Unit Tests: scoring, security utilities, and benchmark runner artifact generation.
- Integration Tests: FastAPI endpoint behavior, login flow, and RBAC permissions.
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
