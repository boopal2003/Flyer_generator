# Dockerfile
FROM python:3.11-slim

# system libs for opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1 FLASK_ENV=production

# serve Flask with Gunicorn on port 8080
CMD ["gunicorn", "-w", "2", "--threads", "4", "-t", "180", "-b", "0.0.0.0:8080", "run:app"]
