FROM python:3.11-slim


WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . /app


RUN chmod +x /app/scripts/*.sh


ENTRYPOINT ["./scripts/entrypoint.sh"]