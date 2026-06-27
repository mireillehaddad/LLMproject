from functools import lru_cache
import json

import numpy as np
from google import genai
from google.genai.types import EmbedContentConfig

from src.common.gcs_utils import download_text, list_blobs
from src.common.settings import settings


TOP_K = 5


def embed_query(client: genai.Client, query: str) -> np.ndarray:
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=query,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768,
        ),
    )

    return np.array(response.embeddings[0].values, dtype=np.float32)


@lru_cache(maxsize=1)
def load_embedding_index():
    records = []
    vectors = []

    embedding_blobs = [
        blob
        for blob in list_blobs(settings.embeddings_prefix)
        if blob.lower().endswith(".jsonl")
    ]

    for blob in embedding_blobs:
        text = download_text(blob)

        for line in text.splitlines():
            if not line.strip():
                continue

            record = json.loads(line)

            if record.get("embedding"):
                record["embedding_blob"] = blob
                records.append(record)
                vectors.append(record["embedding"])

    matrix = np.array(vectors, dtype=np.float32)

    # Normalize once
    matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

    return records, matrix


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    query_embedding = embed_query(client, question)
    query_embedding = query_embedding / np.linalg.norm(query_embedding)

    records, matrix = load_embedding_index()

    scores = matrix @ query_embedding

    ranked_indices = np.argsort(scores)[::-1]

    unique_records = []
    seen = set()

    for idx in ranked_indices:
        record = records[idx]
        key = record.get("text", "")[:300]

        if key in seen:
            continue

        seen.add(key)

        unique_records.append(
            {
                **record,
                "score": float(scores[idx]),
            }
        )

        if len(unique_records) >= top_k:
            break

    return unique_records