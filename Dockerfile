FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (optional): uncomment if needed for scientific stacks
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

COPY . /app

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn -w 2 -k gevent -b 0.0.0.0:${PORT} app:app"]
