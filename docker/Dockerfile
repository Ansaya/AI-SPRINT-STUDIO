ARG FLAVOR
FROM python:3.8${FLAVOR}

# Install docker
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install --no-install-recommends -y ca-certificates curl git gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt update && apt install docker-ce-cli -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && rm -rf ~/.cache/

RUN git clone https://github.com/Ansaya/TOSCARIZER.git toscarizer && \
    cd toscarizer && \
    pip install . && \
    cd ..  && \
    rm -rf toscarizer

COPY docker/requirements* .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-oscarp.txt \
    && pip install --no-cache-dir -r requirements-space4ai.txt \
    && rm -rf requirements*

COPY . /ai-sprint-studio
RUN cd /ai-sprint-studio \
    && pip install --upgrade pip \
    && python3 -m pip install . \
    && cd .. \
    && rm -r /ai-sprint-studio \
    && mkdir /.cookiecutter_replay/ \
    && chmod 777 -R /.cookiecutter_replay

