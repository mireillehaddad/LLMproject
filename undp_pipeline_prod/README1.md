# Local Setup

## 1. Clone the repository

```bash
git clone https://github.com/mireillehaddad/LLMproject.git
cd LLMproject/undp_pipeline_prod
```

## 2. Install uv

```bash
pip install uv
```

## 3. Install project dependencies

```bash
uv sync
```

---

# Run the Pipeline

Set the project root so Python can find the modules.

### PowerShell

```powershell
$env:PYTHONPATH="."
```

## 1. Ingest UNDP project documents

```bash
uv run python -m src.ingest.run_ingest
```

## 2. Chunk PDF documents

```bash
uv run python -m src.chunk.run_chunk
```

## 3. Generate embeddings

```bash
uv run python -m src.embed.run_embed
```

## 4. Load embeddings into BigQuery

```bash
uv run python -m src.retrieval.load_embeddings_to_bigquery
```

## 5. Run the chatbot locally

```bash
uv run streamlit run src/chatbot/app.py
```