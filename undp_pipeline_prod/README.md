clone the repo:

pip install uv
uv init
uv sync


  Run script by script:
  ## Ingest
```
  $env:PYTHONPATH="."
uv run python -m src.ingest.run_ingest
```
## Chunk

```
  $env:PYTHONPATH="."
uv run python -m src.chunk.run_chunk
```
## Embed
```
$env:PYTHONPATH="."
uv run python -m src.embed.run_embed

```
## Load to bq
```
$env:PYTHONPATH="."
uv run python -m src.retrieval.load_embeddings_to_bigquery
```
## Test chatbot locally
```
$env:PYTHONPATH="."
uv run streamlit run src/chatbot/app.py
```
