FROM artefact.skao.int/ska-tango-images-pytango-builder:9.5.0 AS buildenv
FROM artefact.skao.int/ska-tango-images-pytango-runtime:9.5.0 AS runtime


ARG CAR_PYPI_REPOSITORY_URL=https://artefact.skao.int/repository/pypi-internal
ENV PIP_INDEX_URL=${CAR_PYPI_REPOSITORY_URL}

USER root

WORKDIR /app

# Copy poetry.lock* in case it doesn't exist in the repo
COPY pyproject.toml poetry.lock* ./

COPY tmdata /app/src/tmdata

# Install runtime dependencies and the app
RUN poetry config virtualenvs.create false

# Install ssh client and git in order to push tmdata to artefact
RUN apt-get update && \
    apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*
# create temporary .ssh folder to store ssh key.
RUN mkdir -p /home/tango/.ssh && \
    chown -R tango:tango /home/tango && \
    chmod 700 /home/tango/.ssh

RUN pip install poetry==1.8.3
# Developers may want to add --dev to the poetry export for testing inside a container
RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes && \
    pip install -r poetry-requirements.txt && \
    pip install . && \
    rm poetry-requirements.txt

USER tango

CMD ["python3", "-m", "ska_ost_osd.rest.wsgi"]
