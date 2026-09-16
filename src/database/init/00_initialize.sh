#!/bin/bash

set -euo pipefail

required_vars=(
    "POSTGRES_USER_APP"
    "POSTGRES_PASSWORD_APP"

    "POSTGRES_DB_MAIN"

    "POSTGRES_DB_USERS"


    "POSTGRES_USER_SECURE"
    "POSTGRES_PASSWORD_SECURE"


    "POSTGRES_USER_MIGR"
    "POSTGRES_PASSWORD_MIGR"

)

for variable in "${required_vars[@]}"; do
    if [[ -z "${!variable:-}" ]]; then
        echo "Erreur : variable ${variable} non définie." >&2
        exit 1
    fi
done

for template in /docker-entrypoint-initdb.d/*.sql.pattern; do
    echo "Exécution de ${template##*/}..."
    envsubst < "$template" | psql \
        --set ON_ERROR_STOP=1 \
        --username "$POSTGRES_USER" \
        --dbname "$POSTGRES_DB"
done