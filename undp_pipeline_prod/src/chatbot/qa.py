from google import genai

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

    print("\nRetrieved chunks:")
    print("=" * 80)

    for chunk in chunks:
        print(f"\nScore: {chunk['score']:.4f}")
        print(chunk["text"][:500])

    context = build_context(chunks)

    prompt = f"""
You are a UNDP project assistant.

Answer the question using only the context provided below.
If the answer is not in the context, say that the documents do not provide enough information.

When possible, cite the source number, for example [Source 1].

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
    )

    return response.text, chunks