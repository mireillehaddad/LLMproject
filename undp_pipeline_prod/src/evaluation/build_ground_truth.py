import json
import re
import time
from datetime import datetime, timezone

from google import genai
from google.cloud import bigquery

from src.common.gcs_utils import upload_text
from src.common.settings import settings


DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks_eval"

# Start with a small number while testing.
MAX_CHUNKS = 50

# Generate multiple questions from each selected chunk.
QUESTIONS_PER_CHUNK = 2

SLEEP_SECONDS = 0.5


def table_id() -> str:
    return (
        f"{settings.project_id}."
        f"{DATASET_ID}."
        f"{TABLE_ID}"
    )


def load_sample_chunks(
    client: bigquery.Client,
    max_chunks: int = MAX_CHUNKS,
) -> list[dict]:
    """
    Load a diverse sample of evaluation chunks from BigQuery.

    The filters remove empty or extremely short chunks because they
    usually do not contain enough information to generate good questions.
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
        project_id
    FROM `{table_id()}`
    WHERE
        text IS NOT NULL
        AND LENGTH(TRIM(text)) >= 300
        AND chunk_id IS NOT NULL
    ORDER BY RAND()
    LIMIT @max_chunks
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "max_chunks",
                "INT64",
                max_chunks,
            )
        ]
    )

    rows = client.query(
        sql,
        job_config=job_config,
    ).result()

    chunks = [dict(row.items()) for row in rows]

    print(f"Loaded {len(chunks)} chunks from BigQuery.")

    return chunks


def build_question_prompt(
    chunk: dict,
    questions_per_chunk: int,
) -> str:
    return f"""
You are creating a ground-truth evaluation dataset for a UNDP
project-document question-answering chatbot.

Generate exactly {questions_per_chunk} realistic questions that can be
answered using the document passage below.

Requirements:

1. Each question must be answerable from the passage.
2. Do not refer to "the passage", "the chunk", or "the text".
3. Write questions that a real user might ask a UNDP chatbot.
4. Avoid vague questions such as "What is this project about?"
5. Include important entities in the question when available, such as:
   - country
   - project
   - programme
   - organization
   - budget
   - objective
   - timeline
6. The reference answer must be supported directly by the passage.
7. Keep the answer concise but complete.
8. Return only valid JSON. Do not include Markdown fences.

Return this exact structure:

{{
  "questions": [
    {{
      "question": "A realistic question",
      "reference_answer": "An answer supported by the passage"
    }}
  ]
}}

Document metadata:

Country: {chunk.get("country") or "Unknown"}
Year: {chunk.get("year") or "Unknown"}
Project ID: {chunk.get("project_id") or "Unknown"}
File: {chunk.get("file_name") or "Unknown"}
Page: {chunk.get("page_number") or "Unknown"}

Document passage:

{chunk["text"]}
""".strip()


def clean_json_response(text: str) -> str:
    """
    Remove accidental Markdown code fences if the model returns them.
    """
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


def generate_questions(
    client: genai.Client,
    chunk: dict,
    questions_per_chunk: int = QUESTIONS_PER_CHUNK,
) -> list[dict]:
    prompt = build_question_prompt(
        chunk=chunk,
        questions_per_chunk=questions_per_chunk,
    )

    response = client.models.generate_content(
        model=settings.generation_model,
        contents=prompt,
    )

    response_text = response.text or ""

    if not response_text.strip():
        raise ValueError("Gemini returned an empty response.")

    cleaned_response = clean_json_response(response_text)
    result = json.loads(cleaned_response)

    questions = result.get("questions", [])

    if not isinstance(questions, list):
        raise ValueError(
            "The generated 'questions' value is not a list."
        )

    valid_questions = []

    for item in questions:
        if not isinstance(item, dict):
            continue

        question = str(
            item.get("question") or ""
        ).strip()

        reference_answer = str(
            item.get("reference_answer") or ""
        ).strip()

        if not question or not reference_answer:
            continue

        valid_questions.append(
            {
                "question": question,
                "reference_answer": reference_answer,
            }
        )

    return valid_questions


def make_question_id(
    source_number: int,
    question_number: int,
) -> str:
    return (
        f"q_{source_number:04d}_"
        f"{question_number:02d}"
    )


def build_ground_truth_records(
    generation_client: genai.Client,
    chunks: list[dict],
) -> list[dict]:
    records: list[dict] = []

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    for source_number, chunk in enumerate(
        chunks,
        start=1,
    ):
        chunk_id = chunk["chunk_id"]

        print(
            f"\nGenerating questions for "
            f"{source_number}/{len(chunks)}: "
            f"{chunk_id}"
        )

        try:
            generated_questions = generate_questions(
                client=generation_client,
                chunk=chunk,
            )
        except Exception as exc:
            print(
                f"Failed to generate questions for "
                f"{chunk_id}: {exc}"
            )
            continue

        for question_number, item in enumerate(
            generated_questions,
            start=1,
        ):
            question_id = make_question_id(
                source_number=source_number,
                question_number=question_number,
            )

            records.append(
                {
                    "question_id": question_id,
                    "question": item["question"],
                    "reference_answer": (
                        item["reference_answer"]
                    ),

                    # Initially, the source chunk is known to be relevant.
                    "relevant_chunk_ids": [
                        chunk_id
                    ],

                    # This supports future grouping of overlapping chunks.
                    "evidence_groups": [
                        [chunk_id]
                    ],

                    "source_chunk_id": chunk_id,
                    "source_id": chunk.get("source_id"),
                    "source_pdf_blob": chunk.get(
                        "source_pdf_blob"
                    ),
                    "file_name": chunk.get("file_name"),
                    "page_number": chunk.get(
                        "page_number"
                    ),
                    "chunk_index": chunk.get(
                        "chunk_index"
                    ),
                    "year": chunk.get("year"),
                    "country": chunk.get("country"),
                    "project_id": chunk.get(
                        "project_id"
                    ),
                    "created_at": created_at,
                }
            )

        print(
            f"Generated {len(generated_questions)} "
            f"valid questions."
        )

        time.sleep(SLEEP_SECONDS)

    return records


def save_ground_truth(records: list[dict]) -> None:
    if not records:
        print("No ground-truth records were generated.")
        return

    output_text = "\n".join(
        json.dumps(
            record,
            ensure_ascii=False,
        )
        for record in records
    )

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S")

    destination_blob = (
        f"{settings.eval_ground_truth_prefix}/"
        f"ground_truth_{timestamp}.jsonl"
    )

    upload_text(
        destination_blob,
        output_text,
    )

    print(
        f"\nSaved {len(records)} ground-truth records:"
    )
    print(
        f"gs://{settings.bucket_name}/"
        f"{destination_blob}"
    )


def run() -> None:
    print("Starting ground-truth generation...")

    bigquery_client = bigquery.Client(
        project=settings.project_id
    )

    generation_client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    chunks = load_sample_chunks(
        client=bigquery_client,
    )

    if not chunks:
        print(
            "No evaluation chunks were found in BigQuery."
        )
        return

    records = build_ground_truth_records(
        generation_client=generation_client,
        chunks=chunks,
    )

    save_ground_truth(records)

    print()
    print("Ground-truth generation complete.")
    print(f"Selected chunks: {len(chunks)}")
    print(f"Generated questions: {len(records)}")


if __name__ == "__main__":
    run()

