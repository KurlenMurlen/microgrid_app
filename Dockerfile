FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System build deps for scientific wheels/gevent (safe fallback)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ make libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn -w 2 -k gevent -b 0.0.0.0:${PORT} app:app"]
