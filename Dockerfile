# ─── Builder Stage ───
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libcairo2-dev libpango1.0-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ─── Runtime Stage ───
FROM python:3.11-slim

# Runtime libs for cairosvg, bcrypt, pyswisseph
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libffi8 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

EXPOSE 8000

# Auto-create admin on first boot, then start uvicorn
CMD ["sh", "-c", "python create_admin.py 2>/dev/null; uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2"]