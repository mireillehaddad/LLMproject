from google import genai
from google.cloud import bigquery
from google.genai.types import EmbedContentConfig

from src.common.settings import settings


TOP_K = 5
DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks"


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


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    genai_client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    query_embedding = embed_query(genai_client, question)

    bq_client = bigquery.Client(project=settings.project_id)

    table = f"`{settings.project_id}.{DATASET_ID}.{TABLE_ID}`"

    # Retrieve more candidates, then deduplicate in Python.
    search_top_k = top_k * 20

    sql = f"""
    SELECT
        base.id,
        base.text,
        base.source_pdf_blob,
        base.page_number,
        base.year,
        base.country,
        base.project_id,
        base.embedding_blob,
        distance
    FROM VECTOR_SEARCH(
        TABLE {table},
        'embedding',
        (SELECT @query_embedding AS embedding),
        top_k => @search_top_k,
        distance_type => 'COSINE'
    )
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "query_embedding",
                "FLOAT64",
                query_embedding,
            ),
            bigquery.ScalarQueryParameter(
                "search_top_k",
                "INT64",
                search_top_k,
            ),
        ]
    )

    rows = bq_client.query(sql, job_config=job_config).result()

    results = []
    seen = set()

    for row in rows:
        record = dict(row)

        text_key = normalize_text(record.get("text", ""))[:500]

        dedup_key = (
            record.get("project_id"),
            record.get("page_number"),
            text_key,
        )

        if dedup_key in seen:
            continue

        seen.add(dedup_key)

        record["score"] = 1 - float(record["distance"])
        results.append(record)

        if len(results) >= top_k:
            break

    return results

if __name__ == "__main__":
    test_question = "What projects improve access to clean water?"

    print("Running retrieval test...")
    results = retrieve(test_question, top_k=5)

    print(f"Results found: {len(results)}")

    for index, result in enumerate(results, start=1):
        print()
        print(f"Result {index}")
        print(f"Score: {result.get('score', 0):.4f}")
        print(f"Country: {result.get('country')}")
        print(f"Year: {result.get('year')}")
        print(f"Project ID: {result.get('project_id')}")
        print(f"Page: {result.get('page_number')}")
        print(result.get("text", "")[:500])