# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# (Optional) system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Install deps first (cache layer)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . /app

# Railway provides PORT
ENV PORT=8000
EXPOSE 8000

# Run with gunicorn (production)
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker -w 1 app.main:app --bind 0.0.0.0:${PORT} --timeout 60 --access-logfile - --error-logfile - --capture-output"]
