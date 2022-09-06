FROM python:3.8
LABEL maintainer="Miguel Caballer <micafer1@upv.es>"
LABEL version="0.1"
LABEL description="Base container image for the AI-SPRINT use cases."

ARG GIT_USER=user
ARG GIT_PASSWORD=pass

RUN pip install --upgrade pip
#RUN pip install --no-cache-dir \
#    numpy==1.23.0 \
#    opencv-python==4.4.0.46 \
#    onnx==1.11.0 \
#    onnxruntime==1.11.1 \
#    protobuf==3.20.1

# Install AI-Sprint Lib:
RUN git clone https://$GIT_USER:$GIT_PASSWORD@gitlab.polimi.it/ai-sprint/ai-sprint-design.git && \
    cd ai-sprint-design && \
    pip install . && \
    cd ..  && \
    rm -rf ai-sprint-design

# Install AI-Sprint monitoring Lib:
# https://gitlab.polimi.it/ai-sprint/pymonitoring/

RUN git clone https://$GIT_USER:$GIT_PASSWORD@gitlab.polimi.it/ai-sprint/pymonitoring.git && \
    cd pymonitoring && \
    sed -i '/python_requires/d' setup.cfg && \
    pip install . && \
    cd .. && \
    rm -rf pymonitoring
