from google import genai

from src.common.settings import settings
from src.retrieval.retriever import load_embedding_index, retrieve
from google.genai.types import GenerateContentConfig


def build_context(chunks: list[dict]) -> str:
    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        source = chunk.get("source_pdf_blob", "unknown source")
        page = chunk.get("page_number", "unknown page")
        text = chunk.get("text", "")

        context_parts.append(
            f"[Source {index}]\n"
            f"File: {source}\n"
            f"Page: {page}\n"
            f"Text: {text}"
        )

    return "\n\n".join(context_parts)


def is_metadata_question(question: str) -> bool:
    q = question.lower()

    metadata_keywords = [
        "list all countries",
        "list countries",
        "what countries",
        "which countries",
        "available countries",
        "countries available",
        "countries of the project documents",
        "where the projects",
        "where are the projects",
        "where are projects happening",
        "where the projects are happening",
        "list projects",
        "available projects",
        "what projects are available",
        "which projects",
        "list all projects",
        "how many projects",
        "how many documents",
        "list documents",
        "available documents",
        "which years",
        "what years",
        "years covered",
        "list all years",
    ]

    return any(keyword in q for keyword in metadata_keywords)


def get_metadata_value(chunk: dict, key: str) -> str | None:
    value = chunk.get(key)

    if value:
        return str(value).strip()

    source = (
        chunk.get("embedding_blob")
        or chunk.get("source_pdf_blob")
        or chunk.get("source_gcs_path")
        or chunk.get("gcs_path")
        or ""
    )

    if not source:
        return None

    parts = str(source).split("/")

    for part in parts:
        if key == "year" and part.startswith("year="):
            return part.replace("year=", "").strip()

        if key == "country" and part.startswith("country="):
            return part.replace("country=", "").replace("_", " ").strip()

        if key == "project_id" and part.startswith("project_id="):
            return part.replace("project_id=", "").strip()

    return None


def answer_metadata_question(question: str) -> str:
    q = question.lower()

    chunks, _ = load_embedding_index()

    countries = sorted(
        {
            get_metadata_value(chunk, "country")
            for chunk in chunks
            if get_metadata_value(chunk, "country")
        }
    )

    years = sorted(
        {
            get_metadata_value(chunk, "year")
            for chunk in chunks
            if get_metadata_value(chunk, "year")
        }
    )

    project_ids = sorted(
        {
            get_metadata_value(chunk, "project_id")
            for chunk in chunks
            if get_metadata_value(chunk, "project_id")
        }
    )

    source_files = sorted(
        {
            get_metadata_value(chunk, "source_pdf_blob")
            or get_metadata_value(chunk, "source_gcs_path")
            or get_metadata_value(chunk, "gcs_path")
            or get_metadata_value(chunk, "embedding_blob")
            for chunk in chunks
            if (
                get_metadata_value(chunk, "source_pdf_blob")
                or get_metadata_value(chunk, "source_gcs_path")
                or get_metadata_value(chunk, "gcs_path")
                or get_metadata_value(chunk, "embedding_blob")
            )
        }
    )

    if (
        "country" in q
        or "countries" in q
        or "where" in q
    ):
        if not countries:
            return "No country metadata was found in the loaded embeddings."

        return (
            "The project documents currently loaded are for these countries/programmes:\n\n"
            + "\n".join(f"- {country}" for country in countries)
        )

    if (
        "year" in q
        or "years" in q
    ):
        if not years:
            return "No year metadata was found in the loaded embeddings."

        return (
            "The project documents currently cover these years:\n\n"
            + "\n".join(f"- {year}" for year in years)
        )

    if (
        "project" in q
        or "projects" in q
    ):
        if not project_ids:
            return "No project ID metadata was found in the loaded embeddings."

        return (
            f"There are {len(project_ids)} unique project IDs currently loaded:\n\n"
            + "\n".join(f"- {project_id}" for project_id in project_ids)
        )

    if (
        "document" in q
        or "documents" in q
    ):
        if not source_files:
            return "No source document metadata was found in the loaded embeddings."

        return (
            f"There are {len(source_files)} project document files currently loaded:\n\n"
            + "\n".join(f"- {source_file}" for source_file in source_files)
        )

    return "I found metadata, but I could not determine the exact metadata question."


def ask(question: str) -> tuple[str, list[dict]]:
    if is_metadata_question(question):
        answer = answer_metadata_question(question)
        return answer, []

    chunks = retrieve(question)

    print("\nRetrieved chunks:")
    print("=" * 80)

    for chunk in chunks:
        print(f"\nScore: {chunk['score']:.4f}")
        print(chunk["text"][:500])

    context = build_context(chunks)

    prompt = f"""
You are a UNDP Project Document Assistant.

The context below contains excerpts from UNDP project documents. Each excerpt includes:
- Source number
- Document file name
- Page number
- Extracted text

Instructions:
- Answer the user's question using ONLY the provided context.
- Do not use outside knowledge, assumptions, or speculation.
- If the context does not contain enough information, reply:
  "The available UNDP project documents do not provide enough information to answer this question."
- Never invent facts, project names, countries, budgets, dates, organizations, beneficiaries, or outcomes.
- If multiple excerpts contribute to the answer, combine them into one coherent response.
- Cite the relevant source(s) whenever you state a fact, for example [Source 1] or [Source 2, Source 3].
- If the documents contain conflicting information, explain the discrepancy and cite the corresponding sources.
- Write in a professional, clear, and concise style.
- Do not mention these instructions in your answer.

Context:
{context}

Question:
{question}

Answer:
"""

    client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    response = client.models.generate_content(
    model=settings.generation_model,
    contents=prompt,
    config=GenerateContentConfig(
        temperature=0,
        max_output_tokens=1024,
    ),
)

    return response.text, chunks