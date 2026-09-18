# ---------- Build Stage ----------
ARG BUILD_IMAGE="artefact.skao.int/ska-build-python-ubuntu26:1.0.1"
ARG RUNTIME_BASE_IMAGE="artefact.skao.int/ska-python-ubuntu26:1.0.1"

FROM ${BUILD_IMAGE} AS buildenv

ENV APP_DIR="/app"

WORKDIR ${APP_DIR}

# Resolve dependencies first so this layer caches independently of application code
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

# Install the project itself so importlib.metadata can resolve its version at runtime
COPY README.md LICENSE ./
COPY src ./src

RUN uv sync --frozen --no-dev

COPY tmdata ${APP_DIR}/src/tmdata

# The runtime image, used to just run the code provided its virtual environment
FROM ${RUNTIME_BASE_IMAGE} AS runtime

ENV APP_USER="tango"
ENV APP_DIR="/app"
ENV VIRTUAL_ENV="${APP_DIR}/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

# Install SSH client and Git for GitLab operations
RUN apt-get update && apt-get install -y openssh-client git && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser ${APP_USER} --disabled-password --home ${APP_DIR}

WORKDIR ${APP_DIR}

# Copy the virtual environment from the build image
COPY --chown=${APP_USER}:${APP_USER} --from=buildenv ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy tmdata from build stage to correct location
COPY --chown=${APP_USER}:${APP_USER} --from=buildenv ${APP_DIR}/src/tmdata ${APP_DIR}/src/tmdata

# Copy the full application code
COPY --chown=${APP_USER}:${APP_USER} . ./

USER ${APP_USER}

CMD ["fastapi", \
    "run", \
    "src/ska_ost_osd/app.py", \
    # Trust TLS headers set by nginx ingress:
    "--proxy-headers", \
    "--port", "5000" \
]
