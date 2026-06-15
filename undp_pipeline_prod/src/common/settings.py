import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    project_id: str = os.getenv(
        "PROJECT_ID",
        "undp-project-documents",
    )

    region: str = os.getenv(
        "REGION",
        "northamerica-northeast1",
    )

    bucket_name: str = os.getenv(
        "BUCKET_NAME",
        "undp-project-documents-llm-prod",
    )

    years: tuple[int, ...] = tuple(
        int(year.strip())
        for year in os.getenv(
            "YEARS",
            "2023,2024,2025,2026",
        ).split(",")
        if year.strip()
    )

    countries: tuple[str, ...] = tuple(
        country.strip()
        for country in os.getenv(
            "COUNTRIES",
            "Lebanon,Egypt,Yemen,Iraq,Syria,Morocco,Libya,Prog for Palestinian People",
        ).split(",")
        if country.strip()
    )

    max_new_pdfs: int = int(
        os.getenv(
            "MAX_NEW_PDFS",
            "150",
        )
    )

    raw_prefix: str = os.getenv(
        "RAW_PREFIX",
        "raw",
    )

    processed_prefix: str = os.getenv(
        "PROCESSED_PREFIX",
        "processed",
    )

    embeddings_prefix: str = os.getenv(
        "EMBEDDINGS_PREFIX",
        "embeddings",
    )

    metadata_prefix: str = os.getenv(
        "METADATA_PREFIX",
        "metadata",
    )

    embedding_model: str = os.getenv(
        "EMBEDDING_MODEL",
        "gemini-embedding-001",
    )

    generation_model: str = os.getenv(
        "GENERATION_MODEL",
        "gemini-2.5-flash",
    )


settings = Settings()