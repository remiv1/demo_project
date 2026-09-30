FROM python:3.14-slim

ARG APP_UID=1000
ARG APP_GID=1000

WORKDIR /app

COPY migration/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
	&& addgroup --system --gid "${APP_GID}" appuser \
	&& adduser --system --uid "${APP_UID}" --ingroup appuser --home /app appuser

COPY migration/main /app/main
COPY migration/users /app/users
COPY common /app/common

USER appuser

CMD ["alembic"]