FROM python:3.8

COPY docker/requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY docker/requirements-oscarp.txt requirements-oscarp.txt
RUN pip install --no-cache-dir -r requirements-oscarp.txt

COPY docker/requirements-space4ai.txt requirements-space4ai.txt
RUN pip install --no-cache-dir -r requirements-space4ai.txt

# NOTE: once the repo will be public it will be installed directly from gitlab
# RUN pip install git+https://gitlab.polimi.it/ai-sprint/ai-sprint-design.git

# RUN git clone https://gitlab.polimi.it/ai-sprint/OSCAR-P.git src/aisprint/oscarp
RUN git clone https://gitlab.polimi.it/ai-sprint/space4ai-d.git src/aisprint/space4aid

COPY . /ai-sprint-design
RUN cd /ai-sprint-design && python3 -m pip install .
COPY ./src/aisprint/oscarp/oscarp/executables /bin/oscarp_executables
RUN rm -r /ai-sprint-design

RUN git clone https://gitlab.polimi.it/ai-sprint/toscarizer.git && \
    cd toscarizer && \
    pip install . && \
    cd ..  && \
    rm -rf toscarizer
