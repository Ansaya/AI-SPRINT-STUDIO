FROM ai-sprint/design:1.0

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

COPY main.py .
COPY utils.py .
COPY onnx onnx