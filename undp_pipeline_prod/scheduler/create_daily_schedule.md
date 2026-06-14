# Create Daily Schedule

## Objective

Run the UNDP document pipeline automatically every day.

The pipeline performs:

1. Download new UNDP project PDFs
2. Chunk PDF documents
3. Generate embeddings
4. Update the chatbot knowledge base

---

## Architecture

Cloud Scheduler
→ Cloud Workflow
→ Cloud Run Job: ingest
→ Cloud Run Job: chunk
→ Cloud Run Job: embed

---

## Schedule

Run every day at 06:00 UTC.

Cron expression:

```text
0 6 * * *
```

---

## Create Cloud Scheduler Job

```bash
gcloud scheduler jobs create http undp-daily-pipeline \
    --schedule="0 6 * * *" \
    --uri="WORKFLOW_TRIGGER_URL" \
    --http-method=POST
```

---

## Expected Pipeline Flow

```text
UNDP API
    ↓
Ingest PDFs
    ↓
Store PDFs in GCS raw/
    ↓
Chunk PDFs
    ↓
Store chunks in GCS processed/
    ↓
Generate embeddings
    ↓
Store embeddings in GCS embeddings/
    ↓
Chatbot uses updated knowledge base
```

---

## Monitoring

Verify:

* Cloud Scheduler execution logs
* Cloud Workflow execution logs
* Cloud Run Job logs

---

## Future Improvements

* Weekly full refresh
* Slack or email notification on failure
* Automatic retry logic
* CI/CD deployment with Cloud Build

```
```
