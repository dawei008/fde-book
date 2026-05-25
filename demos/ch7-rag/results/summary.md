# Ch7 RAG comparison

## Headline

| approach | accuracy | P50 latency | P95 latency | $/1k calls | errors |
|---|---|---|---|---|---|
| A_prompting | 31.56% | 1808 ms | 3124 ms | $0.9273 | 0 |
| B_rag | 87.11% | 2098 ms | 3783 ms | $0.3321 | 0 |
| C_rag_rerank | 87.11% | 2537 ms | 3653 ms | $2.7485 | 0 |

## By category (accuracy)

| approach | simple | rag | multi-doc | refusal |
|---|---|---|---|---|
| A_prompting | 0.83 | 0.07 | 0.54 | 0.20 |
| B_rag | 1.00 | 0.95 | 1.00 | 0.20 |
| C_rag_rerank | 1.00 | 0.95 | 1.00 | 0.20 |
