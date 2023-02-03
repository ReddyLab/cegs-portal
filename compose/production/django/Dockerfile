ARG PYTHON_VERSION=3.11.1-slim-bullseye

# define an alias for the specfic python version used in this file.
FROM image-mirror-prod-registry.cloud.duke.edu/library/python:${PYTHON_VERSION} as python

FROM ghcr.io/pyo3/maturin@sha256:8abfe13660da007d878fbadcf3b11eb6f49a677de6ccb8ad50b600af01fc6767 AS maturin

WORKDIR /exp_viz

COPY ./extensions/exp_viz .
RUN maturin build -b pyo3 -i 3.11

# Python build stage
FROM python as python-build-stage

ARG BUILD_ENVIRONMENT=production

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
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
FROM python as python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
  && adduser --system --ingroup django django

RUN echo "deb http://security.debian.org/debian-security/ bullseye-security main contrib non-free" >> /etc/apt/sources.list

# Install required system dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install --no-install-recommends -y \
  # psycopg2 dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  libgmp10 \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*


# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --chown=django:django --from=python-build-stage /usr/src/app/wheels  /wheels/
COPY --chown=django:django --from=maturin /exp_viz/target/wheels/exp_viz-0.1.3-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.whl /wheels

# use wheels to install python dependencies
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint


COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# copy application code to WORKDIR
COPY --chown=django:django . ${APP_HOME}

# make django owner of the WORKDIR directory as well.
RUN chown django:django ${APP_HOME}

# make django owner of the python site-packages dir so third-party
# migrations can be created and run
RUN chown -R django:django /usr/local/lib/python3.11/site-packages

USER django

ENTRYPOINT ["/entrypoint"]
