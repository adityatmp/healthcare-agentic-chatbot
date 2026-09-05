# Evaluation Framework & Benchmark Suite

## Metrics
1. **Retrieval Hit Rate**: Percentage of queries where relevant document page is returned in Top-K.
2. **Groundedness Ratio**: Percentage of statements in LLM response backed by context.
3. **Abstention Accuracy**: Correctly rejecting queries where vector store lacks supporting context.
4. **Refusal Correctness**: Safely refusing direct clinical diagnosis or prescription requests.
