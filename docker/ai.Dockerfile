# Dockerfile for standalone AI training and inference engine
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY AI/requirements.txt ./ai_requirements.txt
RUN pip install --no-cache-dir -r ai_requirements.txt

COPY AI/ ./AI/
COPY requirements.txt ./root_requirements.txt
RUN pip install --no-cache-dir -r root_requirements.txt

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["python", "-m", "AI.agents.orchestrator"]
