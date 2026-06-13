# Create a new project folder

```bash
mkdir undp_pipeline
cd undp_pipeline
```

# Create a virtual environment

```bash
uv venv
.venv\Scripts\activate
```

# Install required packages

```bash
uv pip install requests google-cloud-storage python-dotenv langdetect --link-mode=copy
```

# Authenticate with GCP

```bash
gcloud auth application-default login
```

This allows Python to use your Google Cloud credentials.

# Test upload to your bucket

Create `test_upload.py`

```python
from google.cloud import storage

bucket_name = "undp-project-documents-llm-2026"

client = storage.Client()
bucket = client.bucket(bucket_name)

blob = bucket.blob("test.txt")
blob.upload_from_string("Hello UNDP")

print("Uploaded successfully")
```

Run:

```bash
python test_upload.py
```

Verify the file exists:

```bash
gcloud storage ls gs://undp-project-documents-llm-2026
```

Expected output:

```text
gs://undp-project-documents-llm-2026/test.txt
```

# Create the ingestion script

Create:

```text
ingest_undp_pdfs.py
```

This script will:
- Call the UNDP API
- Retrieve project documents for 2026
- Download PDFs
- Upload them to GCS

Run:

```bash
python ingest_undp_pdfs.py
```