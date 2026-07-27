# Architecture Documentation

## Layers

1. Data Layer: synthetic CSV data and PostgreSQL schema.
2. Retrieval Layer: ingestion, cleaning, chunking, embeddings, FAISS indexing, retrieval and reranking.
3. Recommendation Layer: weighted scoring and explainability logic.
4. API Layer: FastAPI endpoints for recommendation, chat, analytics, bench, and utilization.
5. Presentation Layer: React dashboard with KPI widgets and charts.

## End-to-End Flow

1. Generate synthetic workforce and project data.
2. Build embedding index from employee profile documents.
3. Retrieve candidate employees for a project requirement.
4. Apply weighted scoring and produce ranked recommendations.
5. Serve insights through API and dashboard.

## Architecture Diagram Description

User -> React Dashboard -> FastAPI -> (RAG Pipeline + Recommendation Engine + Analytics) -> FAISS + CSV/PostgreSQL + Ollama
