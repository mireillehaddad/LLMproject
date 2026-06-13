import json
import numpy as np

from google.cloud import storage
from google import genai
from sentence_transformers import SentenceTransformer

BUCKET_NAME = "undp-project-documents-llm-2026"
PROJECT_ID = "undp-project-documents"
LOCATION = "us-central1"

EMBEDDINGS_PREFIX = "embeddings"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"

TOP_K = 5


def load_embeddings_from_gcs(bucket_name: str) -> list[dict]:
    storage_client = storage.Client()
    blobs = storage_client.list_blobs(bucket_name, prefix=EMBEDDINGS_PREFIX)

    rows = []

    for blob in blobs:
        if not blob.name.endswith("_embeddings.jsonl"):
            continue

        print(f"Loading: gs://{bucket_name}/{blob.name}")
        content = blob.download_as_text(encoding="utf-8")

        for line in content.splitlines():
            if line.strip():
                rows.append(json.loads(line))

    return rows


def cosine_similarity(query_vector: np.ndarray, document_vectors: np.ndarray) -> np.ndarray:
    return document_vectors @ query_vector


def retrieve_top_chunks(question: str, rows: list[dict], model, top_k: int = TOP_K) -> list[dict]:
    query_vector = model.encode(question, normalize_embeddings=True)

    document_vectors = np.array(
        [row["embedding"] for row in rows],
        dtype=np.float32,
    )

    scores = cosine_similarity(query_vector, document_vectors)
    sorted_indices = np.argsort(scores)[::-1]

    top_results = []
    seen = set()

    for index in sorted_indices:
        row = rows[index]

        dedupe_key = (
            row.get("project_id"),
            row.get("file_name"),
            row.get("page_number"),
        )

        if dedupe_key in seen:
            continue

        seen.add(dedupe_key)

        result = row.copy()
        result["score"] = float(scores[index])
        top_results.append(result)

        if len(top_results) >= top_k:
            break

    return top_results


def build_context(chunks: list[dict]) -> str:
    context_parts = []

    for i, chunk in enumerate(chunks, start=1):
        source_header = (
            f"[Source {i}]\n"
            f"Country: {chunk.get('country')}\n"
            f"Year: {chunk.get('year')}\n"
            f"Project ID: {chunk.get('project_id')}\n"
            f"File: {chunk.get('file_name')}\n"
            f"Page: {chunk.get('page_number')}\n"
        )

        context_parts.append(
            source_header + "\n" + chunk.get("text", "")
        )

    return "\n\n".join(context_parts)


def generate_answer(question: str, chunks: list[dict]) -> str:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

    context = build_context(chunks)

    prompt = f"""
You are a helpful assistant answering questions about UNDP project documents.

Use ONLY the context below.
If the answer is not found in the context, say:
"The provided UNDP documents do not contain enough information to answer this question."

When you answer, cite the sources using [Source 1], [Source 2], etc.

Question:
{question}

Context:
{context}

Answer:
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text


def print_sources(chunks: list[dict]):
    print("\nSources used:")
    print("=" * 80)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n[Source {i}]")
        print(f"Score: {chunk.get('score'):.4f}")
        print(f"Country: {chunk.get('country')}")
        print(f"Year: {chunk.get('year')}")
        print(f"Project ID: {chunk.get('project_id')}")
        print(f"File: {chunk.get('file_name')}")
        print(f"Page: {chunk.get('page_number')}")
        print(f"GCS Path: {chunk.get('source_gcs_path')}")


def main():
    question = input("\nAsk a question about the UNDP documents: ").strip()

    if not question:
        print("No question entered.")
        return

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    print("\nLoading embeddings from GCS...")
    rows = load_embeddings_from_gcs(BUCKET_NAME)

    if not rows:
        print("No embeddings found.")
        return

    print(f"Loaded {len(rows)} chunks.")

    print("\nRetrieving relevant chunks...")
    top_chunks = retrieve_top_chunks(question, rows, embedding_model, TOP_K)

    print("\nGenerating answer with Gemini...")
    answer = generate_answer(question, top_chunks)

    print("\nAnswer:")
    print("=" * 80)
    print(answer)

    print_sources(top_chunks)


if __name__ == "__main__":
    main()