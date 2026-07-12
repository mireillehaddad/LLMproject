import json
import time
from datetime import datetime, timezone
from statistics import mean

from src.common.gcs_utils import (
    download_text,
    list_blobs,
    upload_text,
)
from src.common.settings import settings
from src.evaluation.hybrid_retrieval_eval import retrieve




TOP_K = 10
SLEEP_SECONDS = 0.1

GROUND_TRUTH_PREFIX = "evaluation/ground_truth"
RESULTS_PREFIX = "evaluation/results/hybrid"





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
    ground_truth_record: dict,
    top_k: int,
) -> dict:
    question = ground_truth_record["question"]

    relevant_ids = ground_truth_record[
        "relevant_chunk_ids"
    ]

    retrieved_results = retrieve(
        question=question,
        top_k=top_k,
    )

    retrieved_ids = [
        str(result["id"])
        for result in retrieved_results
        if result.get("id") is not None
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
            "table_id": (
                f"{settings.project_id}."
                "undp_rag.rag_chunks_eval"
               ),
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
        "table_id": (
    f"{settings.project_id}."
    "undp_rag.rag_chunks_eval"
),
        "embedding_model": (
            settings.embedding_model
        ),
       
        "retrieval_method": (
    "hybrid_vector_keyword_rrf"
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
        f"hybrid_retrieval_details_{timestamp}.jsonl"
    )

    summary_blob = (
        f"{RESULTS_PREFIX}/"
        f"hybrid_retrieval_summary_{timestamp}.json"
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
    print("Hybrid retrieval evaluation summary")

    ground_truth_blob, ground_truth_records = (
        load_ground_truth()
    )

    if not ground_truth_records:
        print(
            "No valid ground-truth questions "
            "were found."
        )
        return

   

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
    ground_truth_record=ground_truth_record,
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

