#!/usr/bin/env sh
set -eu

: "${FLASK_SECRET_KEY:?La variable FLASK_SECRET_KEY est requise}"

mkdir -p /tmp/gunicorn

exec gunicorn \
	--control-socket /tmp/gunicorn/gunicorn.ctl \
	--bind "0.0.0.0:${PORT:-8001}" \
	--workers "${WORKERS:-2}" \
	main:app
