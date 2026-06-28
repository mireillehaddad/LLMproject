from google import genai
from google.genai.types import GenerateContentConfig

from src.common.settings import settings
from src.retrieval.retriever import retrieve


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


def ask(question: str) -> tuple[str, list[dict]]:
    chunks = retrieve(question)

    if not chunks:
        return (
            "The available UNDP project documents do not provide enough information to answer this question.",
            [],
        )

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
- Do not start a bullet point unless you can complete it.
- If the context is incomplete, write a short sentence instead of an unfinished list.
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
            max_output_tokens=2048,
        ),
    )

    return response.text, chunks