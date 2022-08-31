FROM python:3.8

COPY docker/requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/requirements-oscarp.txt requirements-oscarp.txt
RUN pip install --no-cache-dir -r requirements-oscarp.txt

# NOTE: once the repo will be public it will be installed directly from gitlab
# RUN pip install git+https://gitlab.polimi.it/ai-sprint/ai-sprint-design.git

COPY . /ai-sprint-design
RUN cd /ai-sprint-design && python3 -m pip install .
