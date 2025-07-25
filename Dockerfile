# ---------- Build Stage ----------
ARG BUILD_IMAGE="artefact.skao.int/ska-build-python:0.3.1"
ARG RUNTIME_BASE_IMAGE="artefact.skao.int/ska-python:0.2.3"

FROM $BUILD_IMAGE AS buildenv


# Set up Poetry environment
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1\
    POETRY_CACHE_DIR=/tmp/poetry_cache

ENV APP_DIR="/app"

WORKDIR $APP_DIR

# Copy dependency files early for better caching
COPY pyproject.toml poetry.lock ./
RUN touch README.md

# Install no-root here so we get a docker layer cached with dependencies
# but not app code, to rebuild quickly.
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY tmdata /app/src/tmdata

# The runtime image, used to just run the code provided its virtual environment
FROM $RUNTIME_BASE_IMAGE AS runtime

ENV APP_USER="tango"
ENV APP_DIR="/app"
ENV VIRTUAL_ENV="${APP_DIR}/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# Create non-root user
RUN adduser $APP_USER --disabled-password --home $APP_DIR

WORKDIR $APP_DIR

# Copy the virtual environment from the build image
COPY --chown=$APP_USER:$APP_USER --from=buildenv ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy the full application code
COPY --chown=$APP_USER:$APP_USER . ./

# Install the current application in editable mode into the virtual environment.
# - Ensures app code is linked into the environment.
# - Assumes dependencies were already installed in the build stage.
RUN python -m pip --require-virtualenv install --no-deps -e .

USER ${APP_USER}

CMD ["fastapi", \
    "run", \
    "src/ska_ost_osd/app.py", \
    # Trust TLS headers set by nginx ingress:
    "--proxy-headers", \
    "--port", "5000" \
]
