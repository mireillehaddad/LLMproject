Evaluation pipeline
-------------------
run_chunk_eval.py
        ↓
run_embed_eval.py
        ↓
load_embeddings_eval_to_bigquery.py
        ↓
build_ground_truth.py
        ↓
evaluate_retrieval.py
        ↓
evaluate_generation.py

src/
├── retrieval/
│   
│
└── evaluation/
    ├── run_chunk_eval.py
    ├── run_embed_eval.py
    ├── load_embeddings_eval_to_bigquery.py
    ├── build_ground_truth.py
    ├── evaluate_retrieval.py
    ├── evaluate_generation.py
    └── metrics.py


# Generate evaluation chunks with id added
```
$env:PYTHONPATH="."
uv run python -m src.evaluation.run_chunk_eval
```

# Generate evaluation embeddings
two changes:
settings.eval_processed_prefix for reading chunks, and:
settings.eval_embeddings_prefix for writing embeddings.
```
$env:PYTHONPATH="."
uv run python -m src.evaluation.run_embed_eval
```
```
$env:PYTHONPATH="."
uv run python -m src.evaluation.load_embeddings_eval_to_bigquery

```

# Build the ground-truth dataset
* Read evaluation chunks from undp_rag.rag_chunks_eval.
* Select a manageable sample.
* Ask Gemini to generate realistic questions answerable from each chunk.
* Save each question with the originating chunk_id.
* Write the ground-truth dataset to GCS.
```
$env:PYTHONPATH="."
uv run python -m src.evaluation.build_ground_truth
```
# Evaluate retrieval
* Read this ground-truth JSONL file.
* Embed each question using RETRIEVAL_QUERY.
* Search rag_chunks_eval.
* Collect the top K chunk IDs.
* Compare them against relevant_chunk_ids.
* Calculate:
* Hit Rate@K
* MRR
* Precision@K
* Recall@K

```
$env:PYTHONPATH="."
uv run python -m src.evaluation.evaluate_retrieval
```
============================================================
Retrieval evaluation summary
============================================================
Questions total: 100
Questions evaluated: 100
Questions failed: 0
Hit Rate@10: 0.4400
MRR@10: 0.1797
Mean Precision@10: 0.0440
Mean Recall@10: 0.4400
Mean Evidence-Group Recall@10: 0.4400

# Evaluate hybrid retrieval
src/evaluation/hybrid_retrieval_eval.py


```
$env:PYTHONPATH="."
uv run python -m src.evaluation.hybrid_retrieval_eval

```
Retrieval evaluation summary
============================================================
Questions total: 100
Questions evaluated: 100
Questions failed: 0
Hit Rate@10: 0.5600
MRR@10: 0.2167
Mean Precision@10: 0.0560
Mean Recall@10: 0.5600
Mean Evidence-Group Recall@10: 0.5600
(LLMproject) PS 


Hybrid retrieval using semantic vector search, keyword matching, domain-specific query expansion, and Reciprocal Rank Fusion outperformed vector-only retrieval. Hit Rate@10 increased from 0.44 to 0.56, while MRR@10 increased from 0.1797 to 0.2167.
One caveat: this still evaluates recovery of the exact source chunk used to generate each question. Because your corpus contains overlapping and duplicated content, actual answer retrieval quality may be higher than 56%.


One important insight may emerge: the exact labeled chunk might not always be retrieved, but the answer can still score perfectly because another overlapping or duplicate chunk contains the same evidence. That would confirm that your earlier Hit Rate@10 of 0.56 underestimates actual answer quality.
# Evaluate answer generation
Load the latest ground-truth questions.
Retrieve the top 10 chunks using your evaluation hybrid retriever.
Generate an answer from those chunks.
Ask Gemini to judge the generated answer against:
the reference answer;
the retrieved context.
Calculate average correctness, groundedness, completeness, answer relevance, and hallucination rate.
Save detailed and summary results separately in GCS.

Run the first test with 20 questions:
$env:PYTHONPATH="."
$env:GENERATION_EVAL_MAX_QUESTIONS="20"

uv run python -m src.evaluation.evaluate_generation


$env:PYTHONPATH="."
uv run python -m src.evaluation.evaluate_generation

============================================================
Generation evaluation summary
============================================================
Questions total: 100
Questions evaluated: 100
Questions failed: 0
Mean correctness: 1.6400 / 2
Mean groundedness: 1.9400 / 2
Mean completeness: 1.7000 / 2
Mean answer relevance: 1.9500 / 2
Normalized total score: 0.9038
Hallucination rate: 0.0100
Exact source retrieval rate: 0.5600
Relevant answers: 0.7700
Partly relevant answers: 0.1900
Non-relevant answers: 0.0400
Mean total time/question: 11.87 seconds
