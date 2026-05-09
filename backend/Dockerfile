# backend/Dockerfile — Optimized for Hugging Face Spaces
FROM python:3.11-slim

WORKDIR /app

# ── System deps ────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    gcc g++ curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── Python deps ────────────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Bake model into image ──────────────────────────────────────────────────
ENV SENTENCE_TRANSFORMERS_HOME=/app/.model_cache
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
print('Downloading model...'); \
m = SentenceTransformer('all-MiniLM-L6-v2'); \
print('Model ready:', m.get_sentence_embedding_dimension(), 'dims') \
"

# ── Application code ───────────────────────────────────────────────────────
COPY . .

# ── Runtime environment ────────────────────────────────────────────────────
ENV TRANSFORMERS_OFFLINE=1
ENV HF_DATASETS_OFFLINE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# CRITICAL: Hugging Face uses 7860
ENV PORT=7860

EXPOSE 7860

# ── Start ──────────────────────────────────────────────────────────────────
# Using port 7860 for Hugging Face compatibility
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]