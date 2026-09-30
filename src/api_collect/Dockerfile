FROM python:3.14-slim

ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

COPY src/api_collect/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    addgroup --system --gid "${APP_GID}" appuser && \
    adduser --system --uid "${APP_UID}" --ingroup appuser --home /app appuser

COPY --chown=root:root src/api_collect /app/api_collect
COPY --chown=root:root src/common /app/common

USER appuser

CMD ["python", "-m", "api_collect.main"]