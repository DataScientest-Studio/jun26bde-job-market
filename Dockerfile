# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# System deps if you ever need them can go here (e.g. build-essential)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install
COPY requirements.txt .

RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir flake8 pytest \
 && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy the rest of the repo
COPY . .

RUN chmod +x /app/entrypoint.sh


ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

CMD ["/app/entrypoint.sh"]


