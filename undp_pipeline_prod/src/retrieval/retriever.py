import json

import numpy as np
from google import genai
from google.genai.types import EmbedContentConfig

from src.common.gcs_utils import download_text, list_blobs
from src.common.settings import settings


TOP_K = 5


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_array = np.array(a)
    b_array = np.array(b)

    return float(
        np.dot(a_array, b_array)
        / (np.linalg.norm(a_array) * np.linalg.norm(b_array))
    )


def embed_query(client: genai.Client, query: str) -> list[float]:
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=query,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=768,
        ),
    )

    return response.embeddings[0].values


def load_embeddings() -> list[dict]:
    records = []

    embedding_blobs = [
        blob
        for blob in list_blobs(settings.embeddings_prefix)
        if blob.lower().endswith(".jsonl")
    ]

    for blob in embedding_blobs:
        text = download_text(blob)

        for line in text.splitlines():
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            if "embedding" in record and record["embedding"]:
                record["embedding_blob"] = blob
                records.append(record)

    return records


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    query_embedding = embed_query(client, question)

    records = load_embeddings()

    scored_records = []

    for record in records:
        score = cosine_similarity(
            query_embedding,
            record["embedding"],
        )

        scored_records.append(
            {
                **record,
                "score": score,
            }
        )

    scored_records.sort(
        key=lambda record: record["score"],
        reverse=True,
    )

    unique_records = []
    seen = set()

    for record in scored_records:
        key = record.get("text", "")[:300]

        if key in seen:
            continue

        seen.add(key)
        unique_records.append(record)

        if len(unique_records) >= top_k:
            break

    return unique_records