import json
import time
from datetime import datetime, timezone
from statistics import mean

from google import genai
from google.cloud import bigquery
from google.genai.types import EmbedContentConfig

from src.common.gcs_utils import (
    download_text,
    list_blobs,
    upload_text,
)
from src.common.settings import settings


DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks_eval"

TOP_K = 10
OUTPUT_DIMENSIONALITY = 768
SLEEP_SECONDS = 0.1

GROUND_TRUTH_PREFIX = "evaluation/ground_truth"
RESULTS_PREFIX = "evaluation/results"


def table_id() -> str:
    return (
        f"{settings.project_id}."
        f"{DATASET_ID}."
        f"{TABLE_ID}"
    )


def parse_jsonl(text: str) -> list[dict]:
    records: list[dict] = []

    for line_number, line in enumerate(
        text.splitlines(),
        start=1,
    ):
        line = line.strip()

        if not line:
            continue

        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            print(
                f"Skipping invalid JSON at line "
                f"{line_number}: {exc}"
            )
            continue

        records.append(record)

    return records


def find_latest_ground_truth_blob() -> str:
    blobs = [
        blob
        for blob in list_blobs(GROUND_TRUTH_PREFIX)
        if blob.lower().endswith(".jsonl")
    ]

    if not blobs:
        raise FileNotFoundError(
            "No ground-truth JSONL files found under "
            f"gs://{settings.bucket_name}/"
            f"{GROUND_TRUTH_PREFIX}"
        )

    # Timestamped filenames sort chronologically.
    latest_blob = sorted(blobs)[-1]

    print(f"Using ground-truth file: {latest_blob}")

    return latest_blob


def load_ground_truth() -> tuple[str, list[dict]]:
    blob_name = find_latest_ground_truth_blob()
    text = download_text(blob_name)
    records = parse_jsonl(text)

    valid_records: list[dict] = []

    for record in records:
        question_id = str(
            record.get("question_id") or ""
        ).strip()

        question = str(
            record.get("question") or ""
        ).strip()

        relevant_chunk_ids = record.get(
            "relevant_chunk_ids"
        )

        if not question_id:
            print("Skipping record without question_id.")
            continue

        if not question:
            print(
                f"Skipping {question_id}: "
                "missing question."
            )
            continue

        if not isinstance(relevant_chunk_ids, list):
            print(
                f"Skipping {question_id}: "
                "relevant_chunk_ids is not a list."
            )
            continue

        relevant_chunk_ids = [
            str(chunk_id).strip()
            for chunk_id in relevant_chunk_ids
            if str(chunk_id).strip()
        ]

        if not relevant_chunk_ids:
            print(
                f"Skipping {question_id}: "
                "no relevant chunk IDs."
            )
            continue

        record["relevant_chunk_ids"] = (
            relevant_chunk_ids
        )

        valid_records.append(record)

    print(
        f"Loaded {len(valid_records)} valid "
        "ground-truth questions."
    )

    return blob_name, valid_records


def embed_query(
    client: genai.Client,
    question: str,
) -> list[float]:
    response = client.models.embed_content(
        model=settings.embedding_model,
        contents=question,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=(
                OUTPUT_DIMENSIONALITY
            ),
        ),
    )

    if not response.embeddings:
        raise ValueError(
            "Gemini returned no query embedding."
        )

    embedding = response.embeddings[0].values

    if not embedding:
        raise ValueError(
            "Gemini returned an empty query embedding."
        )

    return [float(value) for value in embedding]


def retrieve_top_k(
    client: bigquery.Client,
    query_embedding: list[float],
    top_k: int = TOP_K,
) -> list[dict]:
    """
    Perform exact cosine-distance retrieval.

    Smaller cosine distance means greater similarity.
    """
    sql = f"""
    SELECT
        chunk_id,
        source_id,
        text,
        source_pdf_blob,
        file_name,
        page_number,
        chunk_index,
        year,
        country,
        project_id,
        COSINE_DISTANCE(
            embedding,
            @query_embedding
        ) AS distance
    FROM `{table_id()}`
    WHERE
        embedding IS NOT NULL
        AND ARRAY_LENGTH(embedding) = @embedding_dimension
    ORDER BY distance ASC
    LIMIT @top_k
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter(
                "query_embedding",
                "FLOAT64",
                query_embedding,
            ),
            bigquery.ScalarQueryParameter(
                "embedding_dimension",
                "INT64",
                OUTPUT_DIMENSIONALITY,
            ),
            bigquery.ScalarQueryParameter(
                "top_k",
                "INT64",
                top_k,
            ),
        ]
    )

    query_job = client.query(
        sql,
        job_config=job_config,
        location=settings.region,
    )

    rows = query_job.result()

    results: list[dict] = []

    for rank, row in enumerate(rows, start=1):
        results.append(
            {
                "rank": rank,
                "chunk_id": row["chunk_id"],
                "source_id": row["source_id"],
                "text": row["text"],
                "source_pdf_blob": (
                    row["source_pdf_blob"]
                ),
                "file_name": row["file_name"],
                "page_number": row["page_number"],
                "chunk_index": row["chunk_index"],
                "year": row["year"],
                "country": row["country"],
                "project_id": row["project_id"],
                "distance": float(row["distance"]),
                "similarity": (
                    1.0 - float(row["distance"])
                ),
            }
        )

    return results


def hit_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    retrieved_set = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)

    return float(
        bool(retrieved_set & relevant_set)
    )


def reciprocal_rank_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    relevant_set = set(relevant_ids)

    for rank, chunk_id in enumerate(
        retrieved_ids[:k],
        start=1,
    ):
        if chunk_id in relevant_set:
            return 1.0 / rank

    return 0.0


def precision_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    retrieved_top_k = retrieved_ids[:k]

    if not retrieved_top_k:
        return 0.0

    relevant_set = set(relevant_ids)

    relevant_retrieved = sum(
        chunk_id in relevant_set
        for chunk_id in retrieved_top_k
    )

    return (
        relevant_retrieved
        / len(retrieved_top_k)
    )


def recall_at_k(
    retrieved_ids: list[str],
    relevant_ids: list[str],
    k: int,
) -> float:
    relevant_set = set(relevant_ids)

    if not relevant_set:
        return 0.0

    retrieved_set = set(retrieved_ids[:k])

    return (
        len(retrieved_set & relevant_set)
        / len(relevant_set)
    )


def evidence_group_recall_at_k(
    retrieved_ids: list[str],
    evidence_groups: list[list[str]],
    k: int,
) -> float | None:
    """
    An evidence group contains equivalent chunks.

    Retrieving any chunk in a group satisfies that group.
    """
    if not evidence_groups:
        return None

    retrieved_set = set(retrieved_ids[:k])

    valid_groups = [
        {
            str(chunk_id).strip()
            for chunk_id in group
            if str(chunk_id).strip()
        }
        for group in evidence_groups
        if isinstance(group, list)
    ]

    valid_groups = [
        group
        for group in valid_groups
        if group
    ]

    if not valid_groups:
        return None

    matched_groups = sum(
        bool(retrieved_set & group)
        for group in valid_groups
    )

    return matched_groups / len(valid_groups)


def find_first_relevant_rank(
    retrieved_ids: list[str],
    relevant_ids: list[str],
) -> int | None:
    relevant_set = set(relevant_ids)

    for rank, chunk_id in enumerate(
        retrieved_ids,
        start=1,
    ):
        if chunk_id in relevant_set:
            return rank

    return None


def evaluate_question(
    embedding_client: genai.Client,
    bigquery_client: bigquery.Client,
    ground_truth_record: dict,
    top_k: int,
) -> dict:
    question = ground_truth_record["question"]
    relevant_ids = ground_truth_record[
        "relevant_chunk_ids"
    ]

    query_embedding = embed_query(
        client=embedding_client,
        question=question,
    )

    retrieved_results = retrieve_top_k(
        client=bigquery_client,
        query_embedding=query_embedding,
        top_k=top_k,
    )

    retrieved_ids = [
        result["chunk_id"]
        for result in retrieved_results
    ]

    evidence_groups = ground_truth_record.get(
        "evidence_groups",
        [],
    )

    group_recall = evidence_group_recall_at_k(
        retrieved_ids=retrieved_ids,
        evidence_groups=evidence_groups,
        k=top_k,
    )

    return {
        "question_id": ground_truth_record[
            "question_id"
        ],
        "question": question,
        "reference_answer": (
            ground_truth_record.get(
                "reference_answer"
            )
        ),
        "relevant_chunk_ids": relevant_ids,
        "evidence_groups": evidence_groups,
        "source_chunk_id": (
            ground_truth_record.get(
                "source_chunk_id"
            )
        ),
        "country": ground_truth_record.get(
            "country"
        ),
        "project_id": ground_truth_record.get(
            "project_id"
        ),
        "top_k": top_k,
        "retrieved_chunk_ids": retrieved_ids,
        "first_relevant_rank": (
            find_first_relevant_rank(
                retrieved_ids=retrieved_ids,
                relevant_ids=relevant_ids,
            )
        ),
        "hit_at_k": hit_at_k(
            retrieved_ids,
            relevant_ids,
            top_k,
        ),
        "reciprocal_rank": reciprocal_rank_at_k(
            retrieved_ids,
            relevant_ids,
            top_k,
        ),
        "precision_at_k": precision_at_k(
            retrieved_ids,
            relevant_ids,
            top_k,
        ),
        "recall_at_k": recall_at_k(
            retrieved_ids,
            relevant_ids,
            top_k,
        ),
        "evidence_group_recall_at_k": (
            group_recall
        ),
        "retrieved_results": retrieved_results,
    }


def average_optional(
    values: list[float | None],
) -> float | None:
    valid_values = [
        value
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return mean(valid_values)


def build_summary(
    results: list[dict],
    top_k: int,
    ground_truth_blob: str,
) -> dict:
    successful_results = [
        result
        for result in results
        if result.get("status") == "success"
    ]

    failed_results = [
        result
        for result in results
        if result.get("status") == "failed"
    ]

    if not successful_results:
        return {
            "ground_truth_blob": ground_truth_blob,
            "table_id": table_id(),
            "top_k": top_k,
            "questions_total": len(results),
            "questions_evaluated": 0,
            "questions_failed": len(
                failed_results
            ),
            "hit_rate_at_k": None,
            "mrr_at_k": None,
            "mean_precision_at_k": None,
            "mean_recall_at_k": None,
            "mean_evidence_group_recall_at_k": (
                None
            ),
        }

    return {
        "ground_truth_blob": ground_truth_blob,
        "table_id": table_id(),
        "embedding_model": (
            settings.embedding_model
        ),
        "embedding_dimension": (
            OUTPUT_DIMENSIONALITY
        ),
        "retrieval_method": (
            "exact_cosine_distance"
        ),
        "top_k": top_k,
        "questions_total": len(results),
        "questions_evaluated": len(
            successful_results
        ),
        "questions_failed": len(
            failed_results
        ),
        "hit_rate_at_k": mean(
            result["hit_at_k"]
            for result in successful_results
        ),
        "mrr_at_k": mean(
            result["reciprocal_rank"]
            for result in successful_results
        ),
        "mean_precision_at_k": mean(
            result["precision_at_k"]
            for result in successful_results
        ),
        "mean_recall_at_k": mean(
            result["recall_at_k"]
            for result in successful_results
        ),
        "mean_evidence_group_recall_at_k": (
            average_optional(
                [
                    result[
                        "evidence_group_recall_at_k"
                    ]
                    for result
                    in successful_results
                ]
            )
        ),
        "evaluated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


def save_results(
    results: list[dict],
    summary: dict,
) -> None:
    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    detailed_blob = (
        f"{RESULTS_PREFIX}/"
        f"retrieval_details_{timestamp}.jsonl"
    )

    summary_blob = (
        f"{RESULTS_PREFIX}/"
        f"retrieval_summary_{timestamp}.json"
    )

    detailed_text = "\n".join(
        json.dumps(
            result,
            ensure_ascii=False,
        )
        for result in results
    )

    summary_text = json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
    )

    upload_text(
        detailed_blob,
        detailed_text,
    )

    upload_text(
        summary_blob,
        summary_text,
    )

    print()
    print("Saved retrieval evaluation details:")
    print(
        f"gs://{settings.bucket_name}/"
        f"{detailed_blob}"
    )

    print("Saved retrieval evaluation summary:")
    print(
        f"gs://{settings.bucket_name}/"
        f"{summary_blob}"
    )


def print_summary(summary: dict) -> None:
    print()
    print("=" * 60)
    print("Retrieval evaluation summary")
    print("=" * 60)

    print(
        f"Questions total: "
        f"{summary['questions_total']}"
    )

    print(
        f"Questions evaluated: "
        f"{summary['questions_evaluated']}"
    )

    print(
        f"Questions failed: "
        f"{summary['questions_failed']}"
    )

    if not summary["questions_evaluated"]:
        print("No questions were successfully evaluated.")
        return

    top_k = summary["top_k"]

    print(
        f"Hit Rate@{top_k}: "
        f"{summary['hit_rate_at_k']:.4f}"
    )

    print(
        f"MRR@{top_k}: "
        f"{summary['mrr_at_k']:.4f}"
    )

    print(
        f"Mean Precision@{top_k}: "
        f"{summary['mean_precision_at_k']:.4f}"
    )

    print(
        f"Mean Recall@{top_k}: "
        f"{summary['mean_recall_at_k']:.4f}"
    )

    evidence_recall = summary.get(
        "mean_evidence_group_recall_at_k"
    )

    if evidence_recall is not None:
        print(
            f"Mean Evidence-Group Recall@{top_k}: "
            f"{evidence_recall:.4f}"
        )


def run() -> None:
    print("Starting retrieval evaluation...")

    ground_truth_blob, ground_truth_records = (
        load_ground_truth()
    )

    if not ground_truth_records:
        print(
            "No valid ground-truth questions "
            "were found."
        )
        return

    embedding_client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    bigquery_client = bigquery.Client(
        project=settings.project_id,
    )

    evaluation_results: list[dict] = []

    total_questions = len(ground_truth_records)

    for index, ground_truth_record in enumerate(
        ground_truth_records,
        start=1,
    ):
        question_id = ground_truth_record[
            "question_id"
        ]

        print()
        print(
            f"Evaluating {index}/{total_questions}: "
            f"{question_id}"
        )

        print(
            f"Question: "
            f"{ground_truth_record['question']}"
        )

        try:
            result = evaluate_question(
                embedding_client=embedding_client,
                bigquery_client=bigquery_client,
                ground_truth_record=(
                    ground_truth_record
                ),
                top_k=TOP_K,
            )

            result["status"] = "success"

            evaluation_results.append(result)

            rank = result["first_relevant_rank"]

            if rank is None:
                print(
                    f"Relevant chunk not found "
                    f"in top {TOP_K}."
                )
            else:
                print(
                    f"First relevant chunk "
                    f"found at rank {rank}."
                )

            print(
                f"Hit@{TOP_K}: "
                f"{result['hit_at_k']:.0f}"
            )

            print(
                f"Reciprocal rank: "
                f"{result['reciprocal_rank']:.4f}"
            )

        except Exception as exc:
            print(
                f"Failed to evaluate "
                f"{question_id}: {exc}"
            )

            evaluation_results.append(
                {
                    "question_id": question_id,
                    "question": (
                        ground_truth_record[
                            "question"
                        ]
                    ),
                    "status": "failed",
                    "error": str(exc),
                }
            )

        time.sleep(SLEEP_SECONDS)

    summary = build_summary(
        results=evaluation_results,
        top_k=TOP_K,
        ground_truth_blob=ground_truth_blob,
    )

    save_results(
        results=evaluation_results,
        summary=summary,
    )

    print_summary(summary)


if __name__ == "__main__":
    run()

