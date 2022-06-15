FROM python:3.8

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN apt update && \
    apt install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Minimize image size 
RUN (apt-get autoremove -y; \
     apt-get autoclean -y)

RUN mkdir /opt/blurry-faces

WORKDIR /opt/blurry-faces/

COPY src/blurry-faces-onnx/main.py .
COPY src/blurry-faces-onnx/utils.py .
COPY onnx onnx_model
