FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENDERECO_SERVIDOR=0.0.0.0 \
    PORTA_SERVIDOR=8000

WORKDIR /app

COPY aplicativo/requirements.txt aplicativo/requirements.txt
RUN pip install --no-cache-dir -r aplicativo/requirements.txt

COPY aplicativo aplicativo

RUN useradd --create-home --uid 1000 usuario_aplicativo
USER usuario_aplicativo

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORTA_SERVIDOR\"]}/api/v1/ufs')"

CMD ["python", "-m", "aplicativo"]
