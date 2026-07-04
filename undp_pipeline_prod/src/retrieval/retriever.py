from google import genai
from google.cloud import bigquery
from google.genai.types import EmbedContentConfig

from src.common.settings import settings


TOP_K = 5
DATASET_ID = "undp_rag"
TABLE_ID = "rag_chunks"
RRF_K = 60


STOPWORDS = {
    "what", "which", "where", "when", "why", "how",
    "who", "whose", "whom",
    "the", "and", "for", "with", "from", "that", "this",
    "these", "those", "there", "their", "they", "them",
    "are", "was", "were", "is", "be", "been", "being",
    "does", "did", "do", "can", "could", "should", "would",
    "about", "summarize", "summary", "list", "show", "give",
    "project", "projects", "document", "documents", "undp",
    "focus", "focused", "related", "support", "supports",
    "improve", "improves", "improving",
}


DOMAIN_EXPANSIONS = {
    "poverty": ["poverty", "poor", "vulnerable", "income", "livelihood", "livelihoods", "social protection", "cash", "resilience"],
    "food": ["food", "nutrition", "agriculture", "farmer", "farmers", "crop", "crops", "harvest", "irrigation", "food security"],
    "health": ["health", "healthcare", "hospital", "clinic", "medical", "medicine", "disease", "epidemic", "vaccination", "nutrition", "maternal", "child", "hygiene"],
    "education": ["education", "school", "schools", "student", "students", "teacher", "teachers", "learning", "training", "skills", "capacity building", "literacy"],
    "gender": ["gender", "women", "woman", "girls", "female", "empowerment", "equality", "gbv", "violence", "inclusion"],
    "water": ["water", "drinking", "potable", "safe", "sanitation", "wastewater", "desalination", "irrigation", "boreholes", "wells", "pumping", "water supply", "water treatment"],
    "energy": ["energy", "renewable", "solar", "wind", "electricity", "electrification", "grid", "battery", "power"],
    "employment": ["employment", "jobs", "livelihoods", "income", "msme", "msmes", "entrepreneurship", "business", "private sector", "economic"],
    "innovation": ["innovation", "technology", "research", "digital", "startup", "industry", "infrastructure", "manufacturing"],
    "inclusion": ["inclusion", "inclusive", "equity", "inequality", "vulnerable", "persons with disabilities", "disability", "minorities"],
    "cities": ["cities", "urban", "municipality", "municipal", "housing", "settlements", "waste management", "transport"],
    "waste": ["waste", "recycling", "circular economy", "resource efficiency", "consumption"],
    "climate": ["climate", "adaptation", "mitigation", "resilience", "disaster", "risk", "flood", "drought", "emissions", "carbon"],
    "marine": ["marine", "ocean", "coastal", "fisheries", "blue economy"],
    "forest": ["forest", "biodiversity", "ecosystem", "wildlife", "land restoration", "nature"],
    "peace": ["peace", "peacebuilding", "conflict", "security", "justice", "rule of law", "social cohesion", "governance"],
    "partnership": ["partnership", "partners", "coordination", "capacity", "cooperation", "stakeholders", "institutions"],
    "digital": [
        "digital", "digitalization", "digitization", "digital transformation",
        "technology", "innovation", "artificial intelligence", "ai",
        "machine learning", "automation", "cloud", "platform", "portal",
        "dashboard", "mobile", "application", "app", "e-government",
        "e-governance", "digital government", "digital public infrastructure",
        "dpi", "digital identity", "digital id", "cybersecurity",
        "cyber security", "data", "data governance", "open data",
        "geospatial", "gis", "remote sensing", "satellite", "blockchain",
        "internet", "connectivity", "broadband", "ict",
    ],
    "refugee": ["refugee", "refugees", "displaced", "idp", "host communities", "humanitarian", "emergency", "crisis", "recovery"],
}


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


def extract_search_terms(question: str) -> list[str]:
    cleaned = question.lower()

    for char in [
        "?", ":", '"', "'", "(", ")", "[", "]", "{", "}",
        "*", "+", "-", "|", "&", "!", "\\", "/", ",", ".", ";",
    ]:
        cleaned = cleaned.replace(char, " ")

    raw_terms = []

    for word in cleaned.split():
        word = word.strip()

        if len(word) < 4:
            continue

        if word in STOPWORDS:
            continue

        raw_terms.append(word)

    expanded_terms = []

    for term in raw_terms:
        expanded_terms.append(term)

        singular = term[:-1] if term.endswith("s") else term

        if term in DOMAIN_EXPANSIONS:
            expanded_terms.extend(DOMAIN_EXPANSIONS[term])

        if singular in DOMAIN_EXPANSIONS:
            expanded_terms.extend(DOMAIN_EXPANSIONS[singular])

    return list(dict.fromkeys(expanded_terms))


def retrieve(question: str, top_k: int = TOP_K) -> list[dict]:
    genai_client = genai.Client(
        vertexai=True,
        project=settings.project_id,
        location=settings.region,
    )

    query_embedding = embed_query(genai_client, question)
    search_terms = extract_search_terms(question)

    bq_client = bigquery.Client(project=settings.project_id)

    table = f"`{settings.project_id}.{DATASET_ID}.{TABLE_ID}`"
    candidate_k = max(top_k * 10, 50)

    sql = f"""
    WITH vector_candidates AS (
        SELECT
            base.id,
            base.text,
            base.source_pdf_blob,
            base.page_number,
            base.year,
            base.country,
            base.project_id,
            base.embedding_blob,
            distance,
            ROW_NUMBER() OVER (ORDER BY distance ASC) AS vector_rank
        FROM VECTOR_SEARCH(
            TABLE {table},
            'embedding',
            (SELECT @query_embedding AS embedding),
            top_k => @candidate_k,
            distance_type => 'COSINE'
        )
    ),

    keyword_candidates AS (
        SELECT
            id,
            text,
            source_pdf_blob,
            page_number,
            year,
            country,
            project_id,
            embedding_blob,
            keyword_score,
            ROW_NUMBER() OVER (ORDER BY keyword_score DESC) AS keyword_rank
        FROM (
            SELECT
                id,
                text,
                source_pdf_blob,
                page_number,
                year,
                country,
                project_id,
                embedding_blob,
                (
                    SELECT COUNTIF(
                        STRPOS(LOWER(text), LOWER(term)) > 0
                    )
                    FROM UNNEST(@search_terms) AS term
                ) AS keyword_score
            FROM {table}
        )
        WHERE keyword_score > 0
        LIMIT @candidate_k
    ),

    combined AS (
        SELECT
            COALESCE(v.id, k.id) AS id,
            COALESCE(v.text, k.text) AS text,
            COALESCE(v.source_pdf_blob, k.source_pdf_blob) AS source_pdf_blob,
            COALESCE(v.page_number, k.page_number) AS page_number,
            COALESCE(v.year, k.year) AS year,
            COALESCE(v.country, k.country) AS country,
            COALESCE(v.project_id, k.project_id) AS project_id,
            COALESCE(v.embedding_blob, k.embedding_blob) AS embedding_blob,
            v.distance,
            v.vector_rank,
            k.keyword_rank,
            k.keyword_score,
            IF(v.vector_rank IS NULL, 0, 1.0 / (@rrf_k + v.vector_rank)) AS vector_rrf_score,
            IF(k.keyword_rank IS NULL, 0, 1.0 / (@rrf_k + k.keyword_rank)) AS keyword_rrf_score
        FROM vector_candidates v
        FULL OUTER JOIN keyword_candidates k
        ON v.id = k.id
    )

    SELECT
        *,
        vector_rrf_score + keyword_rrf_score AS rrf_score,
        IF(distance IS NULL, 0, 1 - distance) AS vector_score
    FROM combined
    ORDER BY
        IF(vector_rank IS NULL, 0, 1) DESC,
        rrf_score DESC
    LIMIT @candidate_k
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
            bigquery.ArrayQueryParameter("search_terms", "STRING", search_terms),
            bigquery.ScalarQueryParameter("candidate_k", "INT64", candidate_k),
            bigquery.ScalarQueryParameter("rrf_k", "INT64", RRF_K),
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

        record["score"] = float(record.get("rrf_score", 0))
        results.append(record)

        if len(results) >= top_k:
            break

    return results


if __name__ == "__main__":
    test_question = "What projects improve access to clean drinking water?"

    print("Running RRF hybrid retrieval test...")
    print(f"Search terms: {extract_search_terms(test_question)}")

    results = retrieve(test_question, top_k=5)

    print(f"Results found: {len(results)}")

    for index, result in enumerate(results, start=1):
        print()
        print(f"Result {index}")
        print(f"RRF Score: {result.get('score', 0):.6f}")
        print(f"Vector Score: {result.get('vector_score', 0):.4f}")
        print(f"Vector Rank: {result.get('vector_rank')}")
        print(f"Keyword Rank: {result.get('keyword_rank')}")
        print(f"Keyword Score: {result.get('keyword_score')}")
        print(f"Country: {result.get('country')}")
        print(f"Year: {result.get('year')}")
        print(f"Project ID: {result.get('project_id')}")
        print(f"Page: {result.get('page_number')}")
        print(result.get("text", "")[:500])