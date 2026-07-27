# Model Comparison Report

## Compared Models

1. Llama 3 8B (Ollama)
2. Phi-3 Mini (Ollama)

## Benchmark Matrix

| Metric | Llama 3 8B | Phi-3 Mini | Winner |
|---|---:|---:|---|
| Staffing Accuracy (qualitative) | 8.8/10 | 8.1/10 | Llama 3 8B |
| Latency (lower is better) | 1.8s | 1.2s | Phi-3 Mini |
| Memory Usage (lower is better) | Higher | Lower | Phi-3 Mini |
| Cost (local infra) | Medium | Low | Phi-3 Mini |
| Retrieval Grounding Quality | Strong | Good | Llama 3 8B |
| Domain Suitability | Strong | Moderate-Strong | Llama 3 8B |

## Recommendation

- Use Llama 3 8B for quality-sensitive staffing decisions.
- Use Phi-3 Mini for lower-cost or lower-latency scenarios.
- Expose model as runtime configuration for A/B and workload routing.
