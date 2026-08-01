FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

ARG INSTALL_DEV=false

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && if [ "$INSTALL_DEV" = "true" ]; then \
        pip install --no-cache-dir black pytest; \
    fi

COPY . .

ENV RUNNING_IN_DOCKER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000
EXPOSE 8050

CMD ["sh", "/app/entrypoint.sh"]