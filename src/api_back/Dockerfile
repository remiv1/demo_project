FROM python:3.14-slim

ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

COPY src/api_back/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    addgroup --system --gid "${APP_GID}" appuser && \
    adduser --system --uid "${APP_UID}" --ingroup appuser --home /app appuser

COPY --chown=root:root src/api_back /app/api_back

RUN chmod 0555 /app/api_back/start.sh

USER appuser

EXPOSE 8000

CMD ["/app/api_back/start.sh"]
