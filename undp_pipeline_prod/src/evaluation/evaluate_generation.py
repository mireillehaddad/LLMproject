import json
import os
import re
import time
from datetime import datetime, timezone
from statistics import mean

from google import genai

from src.common.gcs_utils import (
    download_text,
    list_blobs,
    upload_text,
)
from src.common.settings import settings
from src.evaluation.hybrid_retrieval_eval import retrieve


TOP_K = 10

# Start with 20 while testing.
# Set GENERATION_EVAL_MAX_QUESTIONS=100 later.
MAX_QUESTIONS = int(
    os.getenv(
        "GENERATION_EVAL_MAX_QUESTIONS",
        "20",
    )
)

SLEEP_SECONDS = 0.2

GROUND_TRUTH_PREFIX = "evaluation/ground_truth"
RESULTS_PREFIX = "evaluation/results/generation"


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

        reference_answer = str(
            record.get("reference_answer") or ""
        ).strip()

        if not question_id:
            print("Skipping record without question_id.")
            continue

        if not question:
            print(
                f"Skipping {question_id}: "
                "missing question."
            )
            continue

        if not reference_answer:
            print(
                f"Skipping {question_id}: "
                "missing reference answer."
            )
            continue

        valid_records.append(record)

    if MAX_QUESTIONS > 0:
        valid_records = valid_records[
            :MAX_QUESTIONS
        ]

    print(
        f"Loaded {len(valid_records)} valid "
        "ground-truth questions."
    )

    return blob_name, valid_records


def build_context(
    retrieved_results: list[dict],
) -> str:
    context_parts: list[str] = []

    for source_number, result in enumerate(
        retrieved_results,
        start=1,
    ):
        text = str(
            result.get("text") or ""
        ).strip()

        if not text:
            continue

        source = (
            f"[Source {source_number}]\n"
            f"Chunk ID: {result.get('id')}\n"
            f"Country: {result.get('country')}\n"
            f"Year: {result.get('year')}\n"
            f"Project ID: {result.get('project_id')}\n"
            f"Page: {result.get('page_number')}\n"
            f"Text: {text}"
        )

        context_parts.append(source)

    return "\n\n".join(context_parts)


def generate_answer(
    client: genai.Client,
    question: str,
    context: str,
) -> str:
    prompt = f"""
You are a UNDP project-document question-answering assistant.

Answer the user's question using only the supplied sources.

Rules:

1. Do not use outside knowledge.
2. If the sources do not contain enough information, say:
   "The available project documents do not provide enough information
   to answer this question."
3. Give a concise but complete answer.
4. Cite supporting sources using [Source 1], [Source 2], and so on.
5. Do not cite a source unless it supports the statement.
6. Do not invent facts, numbers, project details, or citations.

Question:

{question}

Sources:

{context}
""".strip()

    response = client.models.generate_content(
        model=settings.generation_model,
        contents=prompt,
    )

    answer = str(
        response.text or ""
    ).strip()

    if not answer:
        raise ValueError(
            "The generation model returned an empty answer."
        )

    return answer


def clean_json_response(text: str) -> str:
    cleaned = text.strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned,
    )

    return cleaned.strip()


def judge_answer(
    client: genai.Client,
    question: str,
    reference_answer: str,
    generated_answer: str,
    context: str,
) -> dict:
    prompt = f"""
You are evaluating a Retrieval-Augmented Generation chatbot.

Evaluate the generated answer using the question, reference answer,
and retrieved context.

Scoring rules:

Correctness:
- 2 = factually consistent with the reference answer
- 1 = partially correct but missing or slightly misstating information
- 0 = incorrect or contradicts the reference answer

Groundedness:
- 2 = all factual claims are supported by the retrieved context
- 1 = mostly supported, but one or more claims are weakly supported
- 0 = contains unsupported or fabricated factual claims

Completeness:
- 2 = covers all important information needed to answer the question
- 1 = covers part of the answer but misses important information
- 0 = does not answer the main question

Answer relevance:
- 2 = directly answers the question
- 1 = partially relevant or unnecessarily indirect
- 0 = irrelevant

Hallucination:
- true if the answer contains factual information not supported by
  the retrieved context
- false otherwise

Overall label:
- "RELEVANT"
- "PARTLY_RELEVANT"
- "NON_RELEVANT"

Instructions:

1. Judge the generated answer, not the quality of the reference wording.
2. A generated answer may use different wording from the reference.
3. A generated answer can still be correct if it is supported by the
   retrieved context and semantically agrees with the reference answer.
4. Do not reward unsupported detail.
5. Return only valid JSON without Markdown fences.

Return this exact structure:

{{
  "correctness": 0,
  "groundedness": 0,
  "completeness": 0,
  "answer_relevance": 0,
  "hallucination": false,
  "overall_label": "PARTLY_RELEVANT",
  "explanation": "Brief explanation of the evaluation."
}}

Question:

{question}

Reference answer:

{reference_answer}

Generated answer:

{generated_answer}

Retrieved context:

{context}
""".strip()

    response = client.models.generate_content(
        model=settings.generation_model,
        contents=prompt,
    )

    response_text = str(
        response.text or ""
    ).strip()

    if not response_text:
        raise ValueError(
            "The judge returned an empty response."
        )

    cleaned_response = clean_json_response(
        response_text
    )

    result = json.loads(cleaned_response)

    return validate_judgment(result)


def validate_score(
    value,
    field_name: str,
) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid {field_name} score: {value}"
        ) from exc

    if score not in {0, 1, 2}:
        raise ValueError(
            f"{field_name} must be 0, 1, or 2."
        )

    return score


def validate_judgment(
    judgment: dict,
) -> dict:
    if not isinstance(judgment, dict):
        raise ValueError(
            "Judge output is not a JSON object."
        )

    correctness = validate_score(
        judgment.get("correctness"),
        "correctness",
    )

    groundedness = validate_score(
        judgment.get("groundedness"),
        "groundedness",
    )

    completeness = validate_score(
        judgment.get("completeness"),
        "completeness",
    )

    answer_relevance = validate_score(
        judgment.get("answer_relevance"),
        "answer_relevance",
    )

    hallucination_value = judgment.get(
        "hallucination"
    )

    if isinstance(hallucination_value, bool):
        hallucination = hallucination_value
    elif str(hallucination_value).lower() in {
        "true",
        "1",
        "yes",
    }:
        hallucination = True
    elif str(hallucination_value).lower() in {
        "false",
        "0",
        "no",
    }:
        hallucination = False
    else:
        raise ValueError(
            "Invalid hallucination value: "
            f"{hallucination_value}"
        )

    overall_label = str(
        judgment.get("overall_label") or ""
    ).strip().upper()

    allowed_labels = {
        "RELEVANT",
        "PARTLY_RELEVANT",
        "NON_RELEVANT",
    }

    if overall_label not in allowed_labels:
        raise ValueError(
            "Invalid overall label: "
            f"{overall_label}"
        )

    explanation = str(
        judgment.get("explanation") or ""
    ).strip()

    return {
        "correctness": correctness,
        "groundedness": groundedness,
        "completeness": completeness,
        "answer_relevance": answer_relevance,
        "hallucination": hallucination,
        "overall_label": overall_label,
        "explanation": explanation,
    }


def evaluate_question(
    generation_client: genai.Client,
    judge_client: genai.Client,
    ground_truth_record: dict,
) -> dict:
    question = ground_truth_record["question"]
    reference_answer = ground_truth_record[
        "reference_answer"
    ]

    retrieval_started_at = time.perf_counter()

    retrieved_results = retrieve(
        question=question,
        top_k=TOP_K,
    )

    retrieval_seconds = (
        time.perf_counter()
        - retrieval_started_at
    )

    context = build_context(
        retrieved_results
    )

    if not context:
        raise ValueError(
            "Retrieval returned no usable context."
        )

    generation_started_at = time.perf_counter()

    generated_answer = generate_answer(
        client=generation_client,
        question=question,
        context=context,
    )

    generation_seconds = (
        time.perf_counter()
        - generation_started_at
    )

    judging_started_at = time.perf_counter()

    judgment = judge_answer(
        client=judge_client,
        question=question,
        reference_answer=reference_answer,
        generated_answer=generated_answer,
        context=context,
    )

    judging_seconds = (
        time.perf_counter()
        - judging_started_at
    )

    retrieved_chunk_ids = [
        str(result["id"])
        for result in retrieved_results
        if result.get("id") is not None
    ]

    relevant_chunk_ids = [
        str(chunk_id)
        for chunk_id in ground_truth_record.get(
            "relevant_chunk_ids",
            [],
        )
    ]

    exact_source_retrieved = bool(
        set(retrieved_chunk_ids)
        & set(relevant_chunk_ids)
    )

    total_score = (
        judgment["correctness"]
        + judgment["groundedness"]
        + judgment["completeness"]
        + judgment["answer_relevance"]
    )

    normalized_total_score = (
        total_score / 8
    )

    return {
        "question_id": ground_truth_record[
            "question_id"
        ],
        "question": question,
        "reference_answer": reference_answer,
        "generated_answer": generated_answer,
        "country": ground_truth_record.get(
            "country"
        ),
        "project_id": ground_truth_record.get(
            "project_id"
        ),
        "source_chunk_id": (
            ground_truth_record.get(
                "source_chunk_id"
            )
        ),
        "relevant_chunk_ids": (
            relevant_chunk_ids
        ),
        "retrieved_chunk_ids": (
            retrieved_chunk_ids
        ),
        "exact_source_retrieved": (
            exact_source_retrieved
        ),
        "top_k": TOP_K,
        "correctness": judgment[
            "correctness"
        ],
        "groundedness": judgment[
            "groundedness"
        ],
        "completeness": judgment[
            "completeness"
        ],
        "answer_relevance": judgment[
            "answer_relevance"
        ],
        "hallucination": judgment[
            "hallucination"
        ],
        "overall_label": judgment[
            "overall_label"
        ],
        "judge_explanation": judgment[
            "explanation"
        ],
        "total_score": total_score,
        "normalized_total_score": (
            normalized_total_score
        ),
        "retrieval_seconds": (
            retrieval_seconds
        ),
        "generation_seconds": (
            generation_seconds
        ),
        "judging_seconds": judging_seconds,
        "total_seconds": (
            retrieval_seconds
            + generation_seconds
            + judging_seconds
        ),
        "retrieved_results": (
            retrieved_results
        ),
    }


def average_optional(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return mean(values)


def build_summary(
    results: list[dict],
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
            "questions_total": len(results),
            "questions_evaluated": 0,
            "questions_failed": len(
                failed_results
            ),
        }

    label_counts = {
        "RELEVANT": 0,
        "PARTLY_RELEVANT": 0,
        "NON_RELEVANT": 0,
    }

    for result in successful_results:
        label = result["overall_label"]
        label_counts[label] += 1

    hallucination_count = sum(
        result["hallucination"]
        for result in successful_results
    )

    exact_source_count = sum(
        result["exact_source_retrieved"]
        for result in successful_results
    )

    return {
        "ground_truth_blob": ground_truth_blob,
        "retrieval_method": (
            "hybrid_vector_keyword_rrf"
        ),
        "generation_model": (
            settings.generation_model
        ),
        "judge_model": (
            settings.generation_model
        ),
        "top_k": TOP_K,
        "questions_total": len(results),
        "questions_evaluated": len(
            successful_results
        ),
        "questions_failed": len(
            failed_results
        ),
        "mean_correctness": mean(
            result["correctness"]
            for result in successful_results
        ),
        "mean_groundedness": mean(
            result["groundedness"]
            for result in successful_results
        ),
        "mean_completeness": mean(
            result["completeness"]
            for result in successful_results
        ),
        "mean_answer_relevance": mean(
            result["answer_relevance"]
            for result in successful_results
        ),
        "mean_normalized_total_score": mean(
            result["normalized_total_score"]
            for result in successful_results
        ),
        "hallucination_rate": (
            hallucination_count
            / len(successful_results)
        ),
        "exact_source_retrieval_rate": (
            exact_source_count
            / len(successful_results)
        ),
        "relevant_rate": (
            label_counts["RELEVANT"]
            / len(successful_results)
        ),
        "partly_relevant_rate": (
            label_counts["PARTLY_RELEVANT"]
            / len(successful_results)
        ),
        "non_relevant_rate": (
            label_counts["NON_RELEVANT"]
            / len(successful_results)
        ),
        "label_counts": label_counts,
        "mean_retrieval_seconds": mean(
            result["retrieval_seconds"]
            for result in successful_results
        ),
        "mean_generation_seconds": mean(
            result["generation_seconds"]
            for result in successful_results
        ),
        "mean_judging_seconds": mean(
            result["judging_seconds"]
            for result in successful_results
        ),
        "mean_total_seconds": mean(
            result["total_seconds"]
            for result in successful_results
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

    details_blob = (
        f"{RESULTS_PREFIX}/"
        f"generation_details_{timestamp}.jsonl"
    )

    summary_blob = (
        f"{RESULTS_PREFIX}/"
        f"generation_summary_{timestamp}.json"
    )

    details_text = "\n".join(
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
        details_blob,
        details_text,
    )

    upload_text(
        summary_blob,
        summary_text,
    )

    print()
    print("Saved generation evaluation details:")
    print(
        f"gs://{settings.bucket_name}/"
        f"{details_blob}"
    )

    print("Saved generation evaluation summary:")
    print(
        f"gs://{settings.bucket_name}/"
        f"{summary_blob}"
    )


def print_summary(
    summary: dict,
) -> None:
    print()
    print("=" * 60)
    print("Generation evaluation summary")
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
        return

    print(
        f"Mean correctness: "
        f"{summary['mean_correctness']:.4f} / 2"
    )

    print(
        f"Mean groundedness: "
        f"{summary['mean_groundedness']:.4f} / 2"
    )

    print(
        f"Mean completeness: "
        f"{summary['mean_completeness']:.4f} / 2"
    )

    print(
        f"Mean answer relevance: "
        f"{summary['mean_answer_relevance']:.4f} / 2"
    )

    print(
        f"Normalized total score: "
        f"{summary['mean_normalized_total_score']:.4f}"
    )

    print(
        f"Hallucination rate: "
        f"{summary['hallucination_rate']:.4f}"
    )

    print(
        f"Exact source retrieval rate: "
        f"{summary['exact_source_retrieval_rate']:.4f}"
    )

    print(
        f"Relevant answers: "
        f"{summary['relevant_rate']:.4f}"
    )

    print(
        f"Partly relevant answers: "
        f"{summary['partly_relevant_rate']:.4f}"
    )

    print(
        f"Non-relevant answers: "
        f"{summary['non_relevant_rate']:.4f}"
    )

    print(
        f"Mean total time/question: "
        f"{summary['mean_total_seconds']:.2f} seconds"
    )


def run() -> None:
    print("Starting generation evaluation...")

    ground_truth_blob, ground_truth_records = (
        load_ground_truth()
    )

    if not ground_truth_records:
        print(
            "No valid ground-truth questions "
            "were found."
        )
        return

    generation_client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    # Separate variable for clarity.
    # It currently uses the same model/client.
    judge_client = generation_client

    evaluation_results: list[dict] = []

    total_questions = len(
        ground_truth_records
    )

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
                generation_client=generation_client,
                judge_client=judge_client,
                ground_truth_record=ground_truth_record,
            )

            result["status"] = "success"
            evaluation_results.append(result)

            print(
                f"Correctness: "
                f"{result['correctness']}/2"
            )

            print(
                f"Groundedness: "
                f"{result['groundedness']}/2"
            )

            print(
                f"Completeness: "
                f"{result['completeness']}/2"
            )

            print(
                f"Answer relevance: "
                f"{result['answer_relevance']}/2"
            )

            print(
                f"Hallucination: "
                f"{result['hallucination']}"
            )

            print(
                f"Overall label: "
                f"{result['overall_label']}"
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
        ground_truth_blob=ground_truth_blob,
    )

    save_results(
        results=evaluation_results,
        summary=summary,
    )

    print_summary(summary)


if __name__ == "__main__":
    run()