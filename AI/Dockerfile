# Start from an NVIDIA-enabled PyTorch runtime for GPU inference
FROM pytorch/pytorch:2.4.0-cuda11.8-cudnn9-runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_HOME=/app \
    MODEL_ROOT=/app/models

WORKDIR ${APP_HOME}

# Install system packages required by pillow and image loaders
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \ 
    && pip install --no-cache-dir -r requirements.txt

COPY . ${APP_HOME}

EXPOSE 8080 9090

CMD ["python", "-m", "server"]
