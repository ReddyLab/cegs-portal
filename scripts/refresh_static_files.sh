#!/usr/bin/env bash
set -euo pipefail


DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${PROD_CEGSPTL_POSTGRESQL_SVC_SERVICE_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
python /app/manage.py collectstatic --noinput -i "*.ecd" -i "*.fd"
kill -s SIGHUP 9 # Maybe the root gunicorn process is always 9? If not, you can find it by checking /proc
