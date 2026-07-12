# Supporting Multiple Relevant Chunks

In a Retrieval-Augmented Generation (RAG) system, a question may have **multiple correct document chunks** rather than a single ground-truth answer.

Instead of storing one relevant document ID:

```python
record["relevant_id"]
```

store a list of relevant document IDs:

```python
record["relevant_ids"]
```

## Compute Relevance

```python
def compute_relevance(record, results):
    relevant_ids = set(record["relevant_ids"])

    return [
        result["id"] in relevant_ids
        for result in results
    ]
```

## Evaluate the Entire Dataset

```python
def compute_relevance_total(ground_truth, search_function):
    relevance_total = []

    for record in ground_truth:
        results = search_function(record["question"])
        relevance = compute_relevance(record, results)
        relevance_total.append(relevance)

    return relevance_total
```

The existing evaluation function remains unchanged:

```python
def evaluate(ground_truth, search_function):
    relevance_total = compute_relevance_total(
        ground_truth,
        search_function,
    )

    return {
        "hit_rate": hit_rate(relevance_total),
        "mrr": mrr(relevance_total),
    }
```

## Metric Interpretation

### Hit Rate@K

Measures whether **at least one relevant chunk** is retrieved within the top *K* results.

> **Question:** Did the retrieval system return any useful document?

---

### Mean Reciprocal Rank (MRR)

Measures the position of the **first relevant chunk** in the ranked results.

> **Question:** How early did the first useful document appear?

Higher values indicate that relevant documents are ranked closer to the top.

---

## Recall@K

When multiple document chunks are considered relevant, **Recall@K** provides a more complete evaluation by measuring how many of the known relevant chunks are retrieved.

```python
def recall_at_k(ground_truth, search_function, k=5):
    scores = []

    for record in ground_truth:
        relevant_ids = set(record["relevant_ids"])
        results = search_function(record["question"])[:k]
        retrieved_ids = {r["id"] for r in results}

        scores.append(
            len(retrieved_ids & relevant_ids) / len(relevant_ids)
        )

    return sum(scores) / len(scores)
```

## Summary

| Metric | Measures | Best Used For |
|---------|----------|---------------|
| **Hit Rate@K** | Whether at least one relevant chunk is retrieved | Basic retrieval success |
| **MRR** | Ranking position of the first relevant chunk | Ranking quality |
| **Recall@K** | Fraction of all relevant chunks retrieved | Questions with multiple valid answers |

Together, these metrics provide a comprehensive evaluation of retrieval performance:

- **Hit Rate@K** answers: *Did the system retrieve any useful information?*
- **MRR** answers: *Was the useful information ranked near the top?*
- **Recall@K** answers: *How much of the relevant information was retrieved?*