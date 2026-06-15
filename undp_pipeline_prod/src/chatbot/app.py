import streamlit as st

from src.chatbot.qa import ask


st.set_page_config(
    page_title="UNDP Project Document Chatbot",
    page_icon="📄",
    layout="wide",
)

st.title("UNDP Project Document Chatbot")

st.write(
    "Ask questions about the UNDP project documents ingested into the RAG pipeline."
)

question = st.text_area(
    "Enter your question",
    placeholder="Example: What digital initiatives are supported in Lebanon?",
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