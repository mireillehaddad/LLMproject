FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install uv

RUN uv sync

ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["uv", "run", "streamlit", "run", "src/chatbot/app.py", "--server.port=8080", "--server.address=0.0.0.0"]