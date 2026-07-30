# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps if you ever need them can go here (e.g. build-essential)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install
COPY requirements.txt .

ARG INSTALL_DEV=false
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALL_DEV" = "true" ]; then pip install --no-cache-dir black pytest; fi

# Copy the rest of the repo
COPY . .

ENV RUNNING_IN_DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["sh", "/app/entrypoint.sh"]


