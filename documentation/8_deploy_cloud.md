First create your uv project properly.

1. Initialize the project

From your project folder:

uv init

This creates:

pyproject.toml
README.md
2. Add dependencies

For example:

uv add streamlit
uv add google-cloud-storage
uv add requests
uv add google-genai
uv add pypdf

After the first uv add, uv will automatically create:

uv.lock

Your project will then look like:

undp-project/
│
├── app.py
├── pyproject.toml
├── uv.lock
└── README.md
3. Create the Dockerfile

Create a file called:

Dockerfile

in the project root.

4. Verify locally

Run:

uv run streamlit run app.py

If the app opens successfully, you're ready for Cloud Run.

5. Before Cloud Run

I recommend getting these working first:

✅ PDF ingestion from UNDP API

✅ Upload PDFs to GCS bucket

✅ Streamlit chatbot locally

Only after those work should you deploy to Cloud Run.

For your UNDP project, a good milestone order is:

Week 1
------
UNDP API
    ↓
Download PDFs
    ↓
Upload PDFs to GCS

Week 2
------
Extract PDF text
    ↓
Chunk text
    ↓
Generate Gemini embeddings

Week 3
------
RAG chatbot in Streamlit

Week 4
------
Deploy to Cloud Run

This will save you a lot of debugging because you'll know the application works locally before introducing Docker and Cloud Run.