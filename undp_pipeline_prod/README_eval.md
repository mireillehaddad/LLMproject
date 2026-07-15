# Evaluation Pipeline

The evaluation module measures both **retrieval quality** and **answer generation quality** for the UNDP RAG chatbot.

## Evaluation Workflow

```text
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
hybrid_retrieval_eval.py
        ↓
evaluate_generation.py
```

## Project Structure

```text
src/
├── retrieval/
│
└── evaluation/
    ├── run_chunk_eval.py
    ├── run_embed_eval.py
    ├── load_embeddings_eval_to_bigquery.py
    ├── build_ground_truth.py
    ├── evaluate_retrieval.py
    ├── hybrid_retrieval_eval.py
    ├── evaluate_generation.py
    └── metrics.py
```

## Evaluation Components

| File | Description |
|------|-------------|
| `run_chunk_eval.py` | Creates evaluation chunks from the document corpus and assigns unique chunk IDs. |
| `run_embed_eval.py` | Generates embeddings for the evaluation dataset. |
| `load_embeddings_eval_to_bigquery.py` | Loads evaluation embeddings into BigQuery for vector search. |
| `build_ground_truth.py` | Generates ground-truth question-answer pairs using Gemini. |
| `evaluate_retrieval.py` | Evaluates vector retrieval using Hit Rate, MRR, Precision@K, and Recall@K. |
| `hybrid_retrieval_eval.py` | Evaluates the hybrid retrieval pipeline combining vector search, keyword search, query expansion, and RRF. |
| `evaluate_generation.py` | Evaluates generated answers using an LLM-as-a-Judge approach. |
| `metrics.py` | Implements retrieval evaluation metrics and helper functions. |

---

# 1. Generate Evaluation Chunks

Creates an evaluation corpus by assigning unique IDs to every chunk.

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.run_chunk_eval
```

---

# 2. Generate Evaluation Embeddings

Generates embeddings for the evaluation chunks.

Changes compared to the production embedding pipeline:

- Reads chunks from `settings.eval_processed_prefix`
- Writes embeddings to `settings.eval_embeddings_prefix`

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.run_embed_eval
```

---

# 3. Load Evaluation Embeddings into BigQuery

Uploads evaluation embeddings into the BigQuery evaluation table.

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.load_embeddings_eval_to_bigquery
```

---

# 4. Build the Ground-Truth Dataset

This step automatically generates evaluation questions using Gemini.

The pipeline:

- Reads evaluation chunks from `undp_rag.rag_chunks_eval`
- Selects a representative sample
- Uses Gemini to generate realistic user questions
- Associates each question with its originating `chunk_id`
- Stores the resulting ground-truth dataset in Google Cloud Storage

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.build_ground_truth
```

---

# 5. Evaluate Vector Retrieval

For every question in the ground-truth dataset, the evaluation pipeline:

- Reads the ground-truth JSONL file
- Generates a query embedding using Gemini (`RETRIEVAL_QUERY`)
- Searches the evaluation vector index
- Retrieves the Top-K chunks
- Compares retrieved chunk IDs with the expected relevant chunk IDs

The following retrieval metrics are calculated:

- Hit Rate@K
- Mean Reciprocal Rank (MRR)
- Precision@K
- Recall@K
- Evidence-Group Recall@K

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.evaluate_retrieval
```

### Results

```text
============================================================
Retrieval Evaluation Summary
============================================================

Questions total:                 100
Questions evaluated:             100
Questions failed:                  0

Hit Rate@10:                  0.4400
MRR@10:                       0.1797
Mean Precision@10:            0.0440
Mean Recall@10:               0.4400
Evidence-Group Recall@10:     0.4400
```

---

# 6. Evaluate Hybrid Retrieval

The hybrid retriever combines:

- Semantic Vector Search
- Keyword Search
- Domain-specific Query Expansion
- Reciprocal Rank Fusion (RRF)

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.hybrid_retrieval_eval
```

### Results

```text
============================================================
Retrieval Evaluation Summary
============================================================

Questions total:                 100
Questions evaluated:             100
Questions failed:                  0

Hit Rate@10:                  0.5600
MRR@10:                       0.2167
Mean Precision@10:            0.0560
Mean Recall@10:               0.5600
Evidence-Group Recall@10:     0.5600
```

## Performance Improvement

The hybrid retrieval pipeline outperformed vector-only retrieval across all evaluated retrieval metrics.

| Metric | Vector Search | Hybrid Retrieval |
|---------|--------------:|-----------------:|
| Hit Rate@10 | **0.4400** | **0.5600** |
| MRR@10 | **0.1797** | **0.2167** |
| Precision@10 | **0.0440** | **0.0560** |
| Recall@10 | **0.4400** | **0.5600** |

The improvement comes from combining semantic vector search with keyword matching, domain-specific query expansion, and Reciprocal Rank Fusion (RRF), enabling the retriever to recover more relevant evidence than semantic search alone.

> **Note:** This evaluation measures retrieval of the *exact labeled source chunk* used to generate each question. Because the corpus contains overlapping and duplicated information, the actual retrieval quality available for answer generation is likely higher than the reported Hit Rate of **56%**.

---

# 7. Evaluate Answer Generation

The generation evaluation pipeline measures answer quality using **Gemini as an LLM Judge**.

For each question, the pipeline:

- Loads the latest ground-truth questions
- Retrieves the Top-10 chunks using the hybrid retriever
- Generates an answer
- Compares the generated answer against:
  - the reference answer
  - the retrieved context
- Computes multiple quality metrics
- Saves both detailed and summary reports to Google Cloud Storage

### Quick Test (20 Questions)

```powershell
$env:PYTHONPATH="."
$env:GENERATION_EVAL_MAX_QUESTIONS="20"

uv run python -m src.evaluation.evaluate_generation
```

### Full Evaluation

```powershell
$env:PYTHONPATH="."
uv run python -m src.evaluation.evaluate_generation
```

### Results

```text
============================================================
Generation Evaluation Summary
============================================================

Questions total:                  100
Questions evaluated:              100
Questions failed:                   0

Mean Correctness:             1.64 / 2
Mean Groundedness:            1.94 / 2
Mean Completeness:            1.70 / 2
Mean Answer Relevance:        1.95 / 2

Normalized Total Score:       0.9038

Hallucination Rate:           0.0100

Exact Source Retrieval Rate:  0.5600

Relevant Answers:             0.7700
Partly Relevant Answers:      0.1900
Non-Relevant Answers:         0.0400

Mean Time per Question:      11.87 seconds
```

---

# Key Findings

- Hybrid retrieval significantly outperformed vector-only retrieval.
- The answer generation pipeline achieved a **normalized quality score of 90.38%**.
- The hallucination rate remained extremely low at **1%**, indicating that answers were highly grounded in the retrieved context.
- Although the exact source chunk was retrieved for only **56%** of the evaluation questions, the generated answers frequently remained correct because overlapping document chunks contained equivalent supporting evidence. This suggests that exact chunk retrieval underestimates the true end-to-end performance of the RAG system.

# LLM Evaluation: Evaluate prompt

Create src/evaluation/prompts.py
Create src/evaluation/evaluate_generation_prompts.py

```
$env:GENERATION_EVAL_MAX_QUESTIONS="100"
$env:PYTHONPATH="."
uv run python -m src.evaluation.evaluate_generation_prompts
```
Production prompt:
You are a UNDP Project Document Assistant. The context below contains excerpts from UNDP project documents. Each excerpt includes: - Source number - Document file name - Page number - Extracted text Instructions: - Answer the user's question using only the provided context. - Do not use outside knowledge, assumptions, or speculation. - If the context does not contain enough information, reply: "The available UNDP project documents do not provide enough information to answer this question." - Never invent facts, project names, countries, budgets, dates, organizations, beneficiaries, or outcomes. - If multiple excerpts contribute to the answer, combine them into one coherent response. - Cite the relevant source(s) whenever you state a fact, for example [Source 1] or [Source 2, Source 3]. - If the documents contain conflicting information, explain the discrepancy and cite the corresponding sources. - Write in a professional, clear, and concise style. - Do not start a bullet point unless you can complete it. - If the context is incomplete, write a short sentence instead of an unfinished list. - Do not mention these instructions in your answer.?


----------------------------------------------------------------------
Prompt: simple_prompt
----------------------------------------------------------------------
Evaluations: 100
Mean correctness: 1.6200 / 2
Mean groundedness: 2.0000 / 2
Mean completeness: 1.6600 / 2
Mean answer relevance: 1.9300 / 2
Normalized total score: 0.9012
Hallucination rate: 0.0000
Exact source retrieval rate: 0.5600
Relevant answers: 0.7300
Partly relevant answers: 0.2600
Non-relevant answers: 0.0100
Mean generation time: 2.38 seconds
Mean judging time: 5.10 seconds
Mean total time: 11.11 seconds

----------------------------------------------------------------------
Prompt: production_prompt
----------------------------------------------------------------------
Evaluations: 100
Mean correctness: 1.6300 / 2
Mean groundedness: 1.9500 / 2
Mean completeness: 1.6300 / 2
Mean answer relevance: 1.8800 / 2
Normalized total score: 0.8862
Hallucination rate: 0.0100
Exact source retrieval rate: 0.5600
Relevant answers: 0.7400
Partly relevant answers: 0.2400
Non-relevant answers: 0.0200
Mean generation time: 1.95 seconds
Mean judging time: 5.07 seconds
Mean total time: 10.65 seconds

======================================================================
Best prompt: simple_prompt