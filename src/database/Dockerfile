FROM docker.io/library/postgres:18-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext-base \
    && rm -rf /var/lib/apt/lists/*

ENV POSTGRES_INITDB_ARGS="--encoding=UTF8 --locale=fr_FR.utf8 --lc-collate=fr_FR.utf8 --lc-ctype=fr_FR.utf8"

WORKDIR /docker-entrypoint-initdb.d

COPY src/database/init/ ./

RUN chmod 0755 ./*.sh \
    && chmod 0644 ./*.sql.pattern \
    && chown -R postgres:postgres /docker-entrypoint-initdb.d