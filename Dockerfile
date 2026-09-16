FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ROADLENS_DATA_DIR=/opt/roadlens/data \
    ROADLENS_MODEL_PATH=/opt/roadlens/models/yolo11n.pt

RUN apt-get update \
    && apt-get install --no-install-recommends -y libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/roadlens

COPY pyproject.toml README.md ./
COPY app ./app
RUN python -m pip install . \
    && python -c "from app.detector import YoloObjectDetector; YoloObjectDetector().load()"

RUN useradd --create-home roadlens \
    && mkdir -p /opt/roadlens/data /opt/roadlens/models \
    && chown -R roadlens:roadlens /opt/roadlens

USER roadlens

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)"

CMD ["roadlens", "--server.address=0.0.0.0", "--server.port=8501"]
