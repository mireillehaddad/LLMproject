how to make the webapp not local

Since you're already using GCP, GCS, and Vertex AI, the best option is Cloud Run.

Your architecture would become:

Users
   ↓
Cloud Run (Streamlit app)
   ↓
Vertex AI Gemini
   ↓
GCS embeddings
   ↓
UNDP knowledge base
Option 1: Cloud Run (Recommended)

Create:

app.py
requirements.txt
Dockerfile

Then:

gcloud builds submit --tag us-central1-docker.pkg.dev/undp-project-documents/rag-chatbot/app

Deploy:

gcloud run deploy undp-rag-chatbot \
  --image us-central1-docker.pkg.dev/undp-project-documents/rag-chatbot/app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

You get:

https://undp-rag-chatbot-xxxxx.run.app

Anyone can access it.

Option 2: Streamlit Community Cloud

Good for demos but not ideal because:

Vertex AI authentication becomes more complex
Less aligned with your GCP project
Option 3: VM

Run:

streamlit run app.py --server.address 0.0.0.0

on a VM.

I would not do this.

For your Zoomcamp project

I would do:

Cloud Storage
+
Vertex AI
+
Cloud Run
+
Streamlit

because it demonstrates:

✅ GCP architecture
✅ RAG pipeline
✅ Deployment
✅ Public web application

What should you do next?

Before deploying, create these files:

requirements.txt
Dockerfile
.gitignore

Then test the Streamlit app locally one last time.

After that, deploy to Cloud Run and you'll have a public URL.