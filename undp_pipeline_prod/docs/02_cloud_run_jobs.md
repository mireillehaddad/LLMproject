# Create Cloud Run Jobs

This step deploys the UNDP pipeline Docker images as Cloud Run Jobs.

Cloud Run Jobs are designed for batch workloads that start, execute, and exit.

The pipeline contains three jobs:

```text
undp-ingest-job
undp-chunk-job
undp-embed-job
```

---

# Architecture

```text
Artifact Registry
        │
        ▼
Cloud Run Job: ingest
        │
        ▼
Cloud Run Job: chunk
        │
        ▼
Cloud Run Job: embed
```

Each job executes a single step of the pipeline.

---

# Prerequisites

Verify the Docker images exist in Artifact Registry:

```powershell
gcloud artifacts docker images list `
  northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline
```

Expected images:

```text
undp-ingest
undp-chunk
undp-embed
```

---

# Deploy Ingestion Job

```powershell
gcloud run jobs deploy undp-ingest-job `
  --image northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-ingest:latest `
  --region northamerica-northeast1
```

Expected result:

```text
Job [undp-ingest-job] successfully deployed.
```

---

# Deploy Chunking Job

```powershell
gcloud run jobs deploy undp-chunk-job `
  --image northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-chunk:latest `
  --region northamerica-northeast1
```

Expected result:

```text
Job [undp-chunk-job] successfully deployed.
```

---

# Deploy Embedding Job

```powershell
gcloud run jobs deploy undp-embed-job `
  --image northamerica-northeast1-docker.pkg.dev/undp-project-documents/undp-pipeline/undp-embed:latest `
  --region northamerica-northeast1
```

Expected result:

```text
Job [undp-embed-job] successfully deployed.
```

---

# Verify Jobs

List all jobs:

```powershell
gcloud run jobs list `
  --region northamerica-northeast1
```

Expected:

```text
undp-ingest-job
undp-chunk-job
undp-embed-job
```

---

# Test Ingestion Job

Run:

```powershell
gcloud run jobs execute undp-ingest-job `
  --region northamerica-northeast1 `
  --wait
```

Expected behavior:

```text
Fetch UNDP projects
Download new PDFs
Upload PDFs to GCS
Create metadata file
```

---

# Test Chunking Job

Run:

```powershell
gcloud run jobs execute undp-chunk-job `
  --region northamerica-northeast1 `
  --wait
```

Expected behavior:

```text
Read PDFs from GCS
Create text chunks
Upload JSONL chunk files
Skip already processed PDFs
```

---

# Test Embedding Job

Run:

```powershell
gcloud run jobs execute undp-embed-job `
  --region northamerica-northeast1 `
  --wait
```

Expected behavior:

```text
Read chunk files
Generate Gemini embeddings
Upload embeddings to GCS
Skip already embedded files
```

---

# View Execution Logs

List executions:

```powershell
gcloud run jobs executions list `
  --job undp-ingest-job `
  --region northamerica-northeast1
```

Describe an execution:

```powershell
gcloud run jobs executions describe EXECUTION_NAME `
  --region northamerica-northeast1
```

Open logs:

```powershell
gcloud logging read `
  "resource.type=cloud_run_job" `
  --limit=50
```

---

# Verify Output in GCS

Expected bucket structure:

```text
gs://undp-project-documents-llm-2026/

raw/
processed/
embeddings/
metadata/
```

Expected contents:

```text
raw/
    PDF documents

processed/
    JSONL chunk files

embeddings/
    Embedded JSONL files

metadata/
    Ingestion metadata CSV files
```

---

# Deliverables

After completing this step:

```text
Cloud Run Jobs

✓ undp-ingest-job
✓ undp-chunk-job
✓ undp-embed-job
```

The pipeline components are now deployed and ready for orchestration using Cloud Workflows and Cloud Scheduler.
