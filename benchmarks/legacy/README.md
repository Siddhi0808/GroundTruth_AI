# Legacy benchmark artifacts (pre-audit)

These files were produced by the original code (`main` @ 69bc01f) and are kept only as a historical record.
They are **not comparable** to `benchmarks/results/`:

- Every verdict in `benchmark_results_1000.json` came from the rule-based fallback judge (Ollama was not running):
  all `reason` strings are rule templates, confidences are the rule constants, and latency averages 63 ms.
- The run most likely used the SQLite keyword-retrieval fallback, not pgvector.
- The rules had been tuned on the same generated cases (no held-out split), and 166 of the 1,000 cases are duplicates.
- Chunking was 500 words with no overlap, which the embedding model truncates at 256 tokens.

The scripts that produced these files were removed (they targeted the old code); they remain in git history at
`tests/test_benchmark*.py` in commit 69bc01f. Use `benchmarks/run_benchmark.py` for current results.
