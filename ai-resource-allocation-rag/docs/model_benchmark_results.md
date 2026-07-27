# Automated Model Benchmark Results

## Summary
| model | avg_latency_seconds | avg_memory_delta_mb | avg_eval_count | success_rate |
| --- | --- | --- | --- | --- |
| llama3:8b | 89.88166666666666 | 2.3146666666666667 | 469.6666666666667 | 1.0 |
| phi3:mini | 75.622 | 0.8409999999999999 | 729.0 | 1.0 |

## Raw Results
| model | prompt | latency_seconds | memory_delta_mb | prompt_eval_count | eval_count | success |
| --- | --- | --- | --- | --- | --- | --- |
| llama3:8b | Find three available Python developers with Azure experience for a healthcare modernization project. | 111.873 | 5.812 | 25 | 474 | True |
| llama3:8b | Recommend two data engineers with cloud certifications and 5+ years experience for a fintech migration. | 74.909 | 0.609 | 29 | 442 | True |
| llama3:8b | Identify bench resources suitable for DevOps automation initiatives in the telecom domain. | 82.863 | 0.523 | 25 | 493 | True |
| phi3:mini | Find three available Python developers with Azure experience for a healthcare modernization project. | 88.245 | 1.043 | 25 | 841 | True |
| phi3:mini | Recommend two data engineers with cloud certifications and 5+ years experience for a fintech migration. | 31.456 | 0.73 | 32 | 309 | True |
| phi3:mini | Identify bench resources suitable for DevOps automation initiatives in the telecom domain. | 107.165 | 0.75 | 29 | 1037 | True |