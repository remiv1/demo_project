FROM python:3.14-slim

ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

COPY src/seed/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && addgroup --system --gid "${APP_GID}" appuser \
    && adduser --system --uid "${APP_UID}" --ingroup appuser --home /app appuser

COPY --chown=root:root src/seed/import_data.py /app/import_data.py
COPY --chown=root:root src/common /app/common
COPY --chown=root:root src/api_worker/__init__.py /app/api_worker/__init__.py
COPY --chown=root:root src/api_worker/repositories /app/api_worker/repositories

ENV PYTHONPATH=/app

USER appuser

CMD ["python", "/app/import_data.py"]