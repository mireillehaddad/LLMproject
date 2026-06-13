# Deploy UNDP Streamlit Chatbot to Google Cloud Run

## 1. Authenticate with Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
```

---

## 2. Select the GCP Project

```bash
gcloud config set project undp-project-documents
```

Verify:

```bash
gcloud config get-value project
```

Expected:

```text
undp-project-documents
```

---

## 3. Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

---

## 4. Create Dockerfile

Create a file named `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8080"]
```

---

## 5. Create .dockerignore

Create a file named `.dockerignore`:

```text
.venv
__pycache__
.env
.git
data
*.pdf
```

---

## 6. Grant Cloud Build Permission

Grant the Compute Engine service account permission to build containers:

```bash
gcloud projects add-iam-policy-binding undp-project-documents \
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"
```

---

## 7. Grant Vertex AI Permission

Grant the Compute Engine service account permission to call Gemini models:

```bash
gcloud projects add-iam-policy-binding undp-project-documents \
  --member="serviceAccount:1097805338474-compute@developer.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

---

## 8. Deploy to Cloud Run

From the project folder:

```bash
gcloud run deploy undp-chatbot \
  --source . \
  --region northamerica-northeast1 \
  --allow-unauthenticated
```

Cloud Run automatically:

* Builds the Docker image
* Stores it in Artifact Registry
* Creates a Cloud Run service
* Exposes a public URL

---

## 9. Verify Deployment

List services:

```bash
gcloud run services list \
  --region northamerica-northeast1
```

Get the service URL:

```bash
gcloud run services describe undp-chatbot \
  --region northamerica-northeast1 \
  --format="value(status.url)"
```

---

## 10. Access the Application

Open:

```text
https://undp-chatbot-1097805338474.northamerica-northeast1.run.app
```

---

## 11. Redeploy After Changes

After modifying the code:

```bash
git add .
git commit -m "Update chatbot"
git push
```

Redeploy:

```bash
gcloud run deploy undp-chatbot \
  --source . \
  --region northamerica-northeast1 \
  --allow-unauthenticated
```

Cloud Run creates a new revision and routes traffic to the latest version automatically.
