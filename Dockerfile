# syntax=docker/dockerfile:1

# --- Builder stage ---
FROM python:3.10-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Final stage ---
FROM python:3.10-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .

# Set environment variables for production
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "src/telegram_scraper.py"] 