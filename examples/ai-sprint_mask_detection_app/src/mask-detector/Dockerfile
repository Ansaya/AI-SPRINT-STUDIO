FROM python:3.8.6-slim-buster

RUN pip install --upgrade pip
RUN pip install --no-cache-dir opencv-python==4.4.0.46 numpy && \
    rm -rf /root/.cache/pip/* && \
    rm -rf /tmp/*

RUN apt update && \
    apt install -y --no-install-recommends libgl1 libglib2.0-0 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir /opt/mask-detector

WORKDIR /opt/mask-detector

COPY src/mask-detector/main.py .
COPY src/mask-detector/cfg cfg

