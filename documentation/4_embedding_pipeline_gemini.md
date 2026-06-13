Keep your current chunks

Do not redo ingestion or chunking.

Keep:

raw/
processed/
2. Delete old sentence-transformer embeddings
gcloud storage rm --recursive gs://undp-project-documents-llm-2026/embeddings/**
3. Install Gemini SDK
uv pip install google-genai --link-mode=copy
4. Enable Vertex AI
gcloud services enable aiplatform.googleapis.com
5. Authenticate
gcloud auth application-default login
gcloud config set project undp-project-documents
6. Create new Gemini embedding script

Create:

embed_undp_chunks_gemini.py

This script will read:

processed/*.jsonl

and create new embeddings using:

gemini-embedding-001
7. Update the Streamlit app

Your new app.py will no longer use:

from sentence_transformers import SentenceTransformer

It will use Gemini for:

question embedding
answer generation
8. Run the new embedding script
python embed_undp_chunks_gemini.py
9. Run the app
streamlit run app.py

Important: document embeddings and question embeddings must come from the same model. So once you switch to Gemini, both must use Gemini.