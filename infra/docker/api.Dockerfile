FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    AUDIO_MODEL_PATH=/models/audio_classifier.pt

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/api/requirements.txt ./requirements.txt
COPY ml/requirements.txt ./requirements-ml.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r requirements-ml.txt

COPY apps/api/ ./
COPY ml/models/audio_classifier.pt /models/audio_classifier.pt
COPY infra/docker/api-entrypoint.sh /usr/local/bin/parrotcare-entrypoint

RUN mkdir -p /app/media && chmod +x /usr/local/bin/parrotcare-entrypoint

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/parrotcare-entrypoint"]
