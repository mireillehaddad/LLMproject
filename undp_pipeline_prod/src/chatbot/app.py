import streamlit as st

from src.chatbot.qa import ask


st.set_page_config(
    page_title="UNDP Project Document Chatbot",
    page_icon="📄",
    layout="wide",
)

st.title("📄 UNDP Project Document Chatbot")

st.write(
    "Ask questions about UNDP project documents ingested into the RAG pipeline."
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
            answer, chunks = ask(question)

        st.subheader("Answer")
        st.write(answer)

        if chunks:
            st.subheader("Sources")

            for i, chunk in enumerate(chunks, start=1):
                with st.expander(
                    f"Source {i} | Score: {chunk['score']:.4f}"
                ):
                    st.write(
                        f"Page Number: {chunk.get('page_number', 'Unknown')}"
                    )

                    st.write(
                        f"Source File: {chunk.get('source_pdf_blob', 'Unknown')}"
                    )

                    st.code(
                        chunk["text"][:1000]
                    )




st.markdown("---")
st.subheader("Example Questions")

st.markdown("""
- What projects are currently active in Lebanon?
- Which UNDP projects focus on climate change?
- What is the budget of a specific project?
- What outcomes are expected from a project?
- Which stakeholders are involved in a project?
""")
st.markdown("---")

st.header("About This Project")

st.subheader("Problem")

st.markdown("""
UNDP publishes project documents in PDF format on the Open UNDP website:

[Open UNDP](https://open.undp.org/)

Finding specific information across hundreds of pages of project documents is difficult and time-consuming.
""")

st.subheader("Solution")


# st.markdown("""
# This project implements a **fully automated Retrieval-Augmented Generation (RAG) pipeline** on Google Cloud Platform for querying UNDP project documents.

# Python ingestion scripts connect to the Open UNDP API to retrieve project metadata and download PDF documents, which are stored in Google Cloud Storage. The documents are processed using custom Python pipelines that extract text, split documents into overlapping chunks, and generate vector embeddings using Vertex AI Gemini Embeddings. These embeddings enable semantic search across the document collection.

# When a user submits a question, the application generates an embedding for the query, performs vector similarity search to retrieve the most relevant document chunks, and provides the retrieved context to Gemini for answer generation. This approach helps ensure that responses are grounded in the source documents rather than relying solely on the language model's knowledge.

# The solution includes a Streamlit chatbot deployed as a serverless application on Cloud Run. The data pipeline is automated using Cloud Run Jobs for ingestion, chunking, and embedding generation, orchestrated through Cloud Workflows and triggered on a schedule by Cloud Scheduler. CI/CD is implemented with GitHub, Cloud Build, Docker, and Artifact Registry to automate image builds, deployments, and application updates.
# """)


st.markdown("""
This project implements a **fully automated Retrieval-Augmented Generation (RAG) pipeline** on Google Cloud Platform for querying UNDP project documents.

- **Data Ingestion:** Python ingestion scripts connect to the Open UNDP API to retrieve project metadata and download PDF documents, which are stored in Google Cloud Storage.

- **Document Processing:** PDF documents are processed using custom Python pipelines that extract text and split documents into overlapping chunks to preserve context and improve retrieval quality.

- **Embedding Generation:** Vector embeddings are generated for each document chunk using **Vertex AI Gemini Embeddings** and stored in Google Cloud Storage.

- **BigQuery Vector Search:** Generated embeddings are loaded into **BigQuery**, where **BigQuery Vector Search** performs semantic similarity search to efficiently retrieve the most relevant document chunks.

- **Retrieval-Augmented Generation (RAG):** When a user submits a question, the application generates an embedding for the query, retrieves the most relevant document chunks using **BigQuery Vector Search**, and provides the retrieved context to **Gemini** to generate grounded answers based only on the UNDP project documents.

- **Application Layer:** A **Streamlit** chatbot provides an interactive interface and is deployed as a serverless application on **Cloud Run**.

- **Pipeline Orchestration:** The data pipeline is automated using **Cloud Run Jobs** for ingestion, document processing, embedding generation, and loading embeddings into BigQuery. The jobs are orchestrated using **Cloud Workflows** and executed on a schedule by **Cloud Scheduler**.

- **CI/CD:** **GitHub**, **Cloud Build**, **Docker**, and **Artifact Registry** automate container image builds, deployments, and application updates.
""")

st.subheader("Data Source")

st.markdown("""
Open UNDP API:

[Open UNDP API Documentation](https://api.open.undp.org/api_documentation/api#!/default/individual_project_data)
""")



