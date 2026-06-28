import os

import streamlit as st

from src.chatbot.qa import ask


st.set_page_config(
    page_title="UNDP Project Document Chatbot",
    page_icon="📄",
    layout="wide",
)

st.title("📄 UNDP Project Document Chatbot")

st.write(
    "Ask questions about UNDP project documents ingested into the Retrieval-Augmented Generation (RAG) pipeline."
)

question = st.text_area(
    "Enter your question",
    placeholder="Example: What projects are currently active in Lebanon?",
    height=120,
)

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Searching documents and generating answer..."):
            answer, sources = ask(question.strip())

        st.subheader("Answer")
        st.write(answer)

        if sources:
            st.subheader("Sources")

            for i, source in enumerate(sources, start=1):
                pdf_name = os.path.basename(
                    source.get("source_pdf_blob", "Unknown")
                )

                with st.expander(
                    f"Source {i} | {pdf_name} | Score: {source['score']:.3f}"
                ):

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown(f"**🌍 Country:** {source.get('country', 'Unknown')}")
                        st.markdown(f"**📅 Year:** {source.get('year', 'Unknown')}")
                        st.markdown(f"**📖 Page:** {source.get('page_number', 'Unknown')}")

                    with col2:
                        st.markdown(f"**🆔 Project ID:** {source.get('project_id', 'Unknown')}")
                        st.markdown(f"**🎯 Similarity:** {source['score']:.3f}")

                    st.markdown(f"**📄 Document:** `{pdf_name}`")

                    st.divider()

                    st.markdown("### Relevant Excerpt")

                    with st.container(border=True):
                        st.write(source.get("text", ""))

st.markdown("---")

st.subheader("Example Questions")

st.markdown("""
- What projects are currently active in Lebanon?
- Which UNDP projects focus on climate change?
- What projects improve access to clean drinking water?
- What is the budget of a specific project?
- What outcomes are expected from a project?
- Which stakeholders are involved in a project?
""")

st.markdown("---")

st.header("About This Project")

st.subheader("Problem")

st.markdown("""
UNDP publishes project documents in PDF format on the **Open UNDP** website:

**https://open.undp.org/**

Finding specific information across hundreds of pages of project documents is difficult and time-consuming.
""")

st.subheader("Solution")

st.markdown("""
### Technical Pipeline Overview

This project implements a fully automated **Retrieval-Augmented Generation (RAG)** pipeline on **Google Cloud Platform** for querying **UNDP project documents**.

- **Data Ingestion:** Python ingestion scripts connect to the **Open UNDP API** to retrieve project metadata and download PDF documents, which are stored in **Google Cloud Storage**.

- **Document Processing:** PDF documents are processed using custom Python pipelines that extract text and split documents into overlapping chunks to preserve context and improve retrieval quality.

- **Embedding Generation:** Each document chunk is converted into a vector embedding using **Vertex AI Gemini Embeddings**.

- **BigQuery Vector Search:** Generated embeddings are loaded into **BigQuery**, where a **BigQuery Vector Index** enables fast semantic similarity search to retrieve the most relevant document chunks.

- **Retrieval-Augmented Generation (RAG):** When a user submits a question, an embedding is generated for the query and compared against the indexed document embeddings in **BigQuery Vector Search**. The retrieved context is then provided to **Gemini**, which generates grounded responses based solely on the retrieved UNDP project documents.

- **Application Layer:** A **Streamlit** chatbot provides an interactive interface and is deployed as a serverless application on **Cloud Run**.

- **Pipeline Orchestration:** The end-to-end pipeline is automated using **Cloud Run Jobs** for data ingestion, document processing, embedding generation, and loading embeddings into BigQuery. These jobs are orchestrated with **Cloud Workflows** and scheduled using **Cloud Scheduler**.

- **CI/CD:** **GitHub**, **Cloud Build**, **Docker**, and **Artifact Registry** automate container image creation, deployment, and application updates.
""")

st.subheader("Data Source")

st.markdown("""
Open UNDP API Documentation:

https://api.open.undp.org/api_documentation/api#!/default/individual_project_data
""")