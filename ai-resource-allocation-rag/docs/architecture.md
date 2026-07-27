# Architecture Documentation

## Layers

1. Data Layer: synthetic CSV data and PostgreSQL schema.
2. Retrieval Layer: ingestion, cleaning, chunking, embeddings, FAISS indexing, retrieval and reranking.
3. Recommendation Layer: weighted scoring and explainability logic.
4. API Layer: FastAPI endpoints for recommendation, constrained chat, analytics, project details, assign/unassign, and cross-project AI chat.
5. Presentation Layer: React dashboard and workforce workspace (Employees + Projects tabs, dedicated project details view).

## End-to-End Flow

1. Generate synthetic workforce and project data.
2. Build embedding index from employee profile documents.
3. Retrieve candidate employees for a project requirement.
4. Apply weighted scoring and produce ranked recommendations.
5. Manage assignment lifecycle (assign/unassign) with utilization updates.
6. Serve insights through API and role-aware UI.

## Role-Aware Experience

- Authentication issues JWT tokens with role claims.
- Backend enforces RBAC for each endpoint.
- Frontend applies role-specific UX:
	- viewer: read-only operations,
	- manager/admin: recommendation + assignment actions.

## Chat Scope Guardrails

- Dashboard chat performs lightweight client-side validation before sending requests.
- Empty, too-short, and non-staffing prompts are blocked in the UI with guidance.
- Chat endpoints accept only staffing/allocation-related queries.
- Out-of-scope prompts return HTTP 400 with a clear supported-scope explanation.

## Architecture Diagram Description

User -> React UI (Dashboard + Workforce) -> FastAPI -> (RAG Pipeline + Recommendation Engine + Analytics + Allocation APIs) -> FAISS + CSV/PostgreSQL + Ollama
