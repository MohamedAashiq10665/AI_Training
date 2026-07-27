# Limitations and Future Enhancements

## Current Limitations

- Synthetic data only, no HRIS integration.
- Basic ranking logic without reinforcement learning.
- Recommendation weighting is mostly static and not yet feedback-trained.
- Chat can still depend on local model availability/runtime health.
- Docker workflow may be affected by host daemon reliability.
- Primary operational persistence can run on SQLite in local mode, which is not ideal for high-concurrency production workloads.

## Future Enhancements

- Real-time ERP/HRMS connectors.
- Learning-to-rank using allocation outcomes.
- Forecasting for demand and bench risk.
- Multi-objective optimization for staffing constraints.
- Fine-grained audit logs for every assignment/unassignment decision with reviewer traces.
- Transfer impact simulator for cross-project movement recommendations.
- Scenario planning workspace for 30/60/90-day demand balancing.
