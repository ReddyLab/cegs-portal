ARG PYTHON_VERSION=3.11.9-slim-bullseye
ARG RUST_VERSION=1.77-bullseye

# define an alias for the specfic python version used in this file.
FROM image-mirror-prod-registry.cloud.duke.edu/library/python:${PYTHON_VERSION} AS python

# Build the rust applications for generating coverage information
FROM image-mirror-prod-registry.cloud.duke.edu/library/rust:${RUST_VERSION} AS rust

WORKDIR /build
RUN git clone https://github.com/ReddyLab/ccgr_portal_cov_viz.git
WORKDIR /build/ccgr_portal_cov_viz/cov_viz
RUN cargo build -r

WORKDIR /build/ccgr_portal_cov_viz/cov_viz_manifest
RUN cargo build -r


FROM ghcr.io/pyo3/maturin@sha256:1c75eb0d2b92999b583b02f699acf4a2ad892c0bf679918d5941f65f9b1bf9a1 AS maturin

WORKDIR /exp_viz

COPY ./extensions/exp_viz .
RUN maturin build -b pyo3 -i 3.11 --release
RUN ls /exp_viz/target/wheels

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=production

RUN echo "deb http://security.debian.org/debian-security/ bullseye-security main contrib non-free" >> /etc/apt/sources.list

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev \
  libgmp10 \
  # Pillow deps
  zlib1g-dev \
  libjpeg-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN python -m pip wheel --wheel-dir /usr/src/app/wheels -r ${BUILD_ENVIRONMENT}.txt

# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN adduser --system --ingroup root django

RUN echo "deb http://security.debian.org/debian-security/ bullseye-security main contrib non-free" >> /etc/apt/sources.list

# Install required system dependencies
RUN apt-get update
RUN apt-get upgrade --no-install-recommends -y
RUN apt-get install --no-install-recommends -y \
  # psycopg dependencies
  libpq-dev \
  python3-dev \
  # Translations dependencies
  gettext \
  libgmp10
# cleaning up unused files
RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false
RUN rm -rf /var/lib/apt/lists/*

# copy rust apps to bin dir
COPY --chown=django:root --from=rust /build/ccgr_portal_cov_viz/cov_viz/target/release/cov_viz  /usr/local/bin/cov_viz
COPY --chown=django:root --from=rust /build/ccgr_portal_cov_viz/cov_viz_manifest/target/release/cov_viz_manifest  /usr/local/bin/cov_viz_manifest

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --chown=django:root --from=python-build-stage /usr/src/app/wheels  /wheels
COPY --chown=django:root --from=maturin /exp_viz/target/wheels/exp_viz-0.4.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl /wheels

# use wheels to install python dependencies
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

COPY --chown=django:root ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint


COPY --chown=django:root ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY --chown=django:root ./compose/production/django/start_huey /start_huey
RUN sed -i 's/\r$//g' /start_huey
RUN chmod +x /start_huey

# copy application code to WORKDIR
COPY --chown=django:root . ${APP_HOME}

# Create media directory for static served files
RUN mkdir -p ${APP_HOME}/static_root
RUN chmod ug+w ${APP_HOME}/static_root

# Create media directory for temporarily served files
RUN mkdir -p ${APP_HOME}/cegs_portal/media/expr_data_dir
RUN chmod ug+w ${APP_HOME}/cegs_portal/media/
RUN chmod ug+w ${APP_HOME}/cegs_portal/media/expr_data_dir

# make django owner of the WORKDIR directory as well.
RUN chown -R django:root ${APP_HOME}

# make django owner of the python site-packages dir so third-party
# migrations can be created and run
RUN chown -R django:root /usr/local/lib/python3.11/site-packages

USER django


ENTRYPOINT ["/entrypoint"]
