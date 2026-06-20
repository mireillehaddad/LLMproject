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

st.header("About This Project")

st.subheader("Problem")

st.markdown("""
UNDP publishes project documents in PDF format on the Open UNDP website:

[Open UNDP](https://open.undp.org/)

Finding specific information across hundreds of pages of project documents is difficult and time-consuming.
""")

st.subheader("Solution")

st.markdown("""
This project builds a **Retrieval-Augmented Generation (RAG) chatbot** that allows users to ask questions about UNDP project documents and receive accurate answers grounded in the source documents.

The UNDP project documents are used as the knowledge base of the chatbot.

The system automatically:

1. Ingests UNDP project documents using the Open UNDP API.
2. Downloads and processes PDF documents.
3. Splits documents into chunks.
4. Creates vector embeddings for semantic search.
5. Retrieves the most relevant document chunks for a user query.
6. Uses Gemini to generate answers based on the retrieved context.
7. Provides a web interface built with Streamlit and deployed on Google Cloud Run.
""")

st.subheader("Data Source")

st.markdown("""
Open UNDP API:

[Open UNDP API Documentation](https://api.open.undp.org/api_documentation/api#!/default/individual_project_data)
""")

st.subheader("Architecture")

st.code("""
Open UNDP API
       │
       ▼
PDF Documents
       │
       ▼
Document Processing
       │
       ▼
Chunking
       │
       ▼
Embeddings Generation
       │
       ▼
Vector Search
       │
       ▼
Relevant Context Retrieval
       │
       ▼
Gemini
       │
       ▼
Streamlit Web Application
""")

st.subheader("Web Application")

st.markdown("""
The chatbot is available at:

[UNDP Chatbot Web App](https://undp-chatbot-1097805338474.northamerica-northeast1.run.app/)
""")

st.subheader("Features")

st.markdown("""
- Automatic ingestion of UNDP project documents
- PDF processing and chunking
- Semantic search using embeddings
- Retrieval-Augmented Generation (RAG)
- Gemini-powered question answering
- Streamlit user interface
- Deployment on Google Cloud Run
""")

st.subheader("Example Questions")

st.markdown("""
- What projects are currently active in Lebanon?
- Which UNDP projects focus on climate change?
- What is the budget of a specific project?
- What outcomes are expected from a project?
- Which stakeholders are involved in a project?
""")