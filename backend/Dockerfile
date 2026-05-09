# backend/Dockerfile
# Production Dockerfile for Koyeb free tier
# Strategy: bake the sentence-transformers model into the image
# so no HuggingFace DNS is needed at runtime (blocked by some ISPs)

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

# ── Bake model into image (no runtime DNS needed) ──────────────────────────
# Downloads ~90MB during build — never again at runtime
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
ENV PORT=8005

EXPOSE 8005

# ── Health check ───────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# ── Start ──────────────────────────────────────────────────────────────────
# Single worker — Koyeb free tier has 512MB RAM
# --timeout-keep-alive 65 keeps connection alive through Koyeb's proxy
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8005", \
     "--workers", "1", \
     "--timeout-keep-alive", "65"]