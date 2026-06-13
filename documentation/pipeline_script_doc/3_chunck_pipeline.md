Create a new script:
```
chunk_undp_pdfs.py

```
Install PDF package first:
```
uv pip install pypdf --link-mode=copy
```
Then the script should:

Read PDFs from:
```
raw/year=2026/country=Lebanon/
raw/year=2026/country=Egypt/
```

Extract text.
Split into chunks, for example 800–1000 characters each.
Save to:
```
processed/year=2026/country=Lebanon/project_id=.../chunks.jsonl
```
After that, we create embeddings from chunks.jsonl.

# Create

chunk_undp_pdfs.py

Run it:

```
python chunk_undp_pdfs.py
```
Those Egypt PDFs are probably scanned/image-based PDFs, so pypdf cannot extract text.

For now your pipeline is still good:

6 PDFs processed successfully
6 PDFs need OCR later

Next simple fix: mark scanned PDFs in GCS so you can process them later with OCR.

Add this idea later:

ocr_needed/
  year=2025/
    country=Egypt/
      project_id=00126312/
        3365773_Project_Document.pdf


For now we will continue without OCR.


# Create embeddings from the processed/*.jsonl files


Your flow now is:

raw PDFs
  ↓
processed chunks JSONL
  ↓
embeddings
  ↓
vector search
  ↓
chatbot

For OCR later, we can use one of these:

Google Document AI
Cloud Vision OCR
pytesseract locally

