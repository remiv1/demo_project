#!/bin/sh

set -eu

: "${REDIS_APPLICATION_PASSWORD:?La variable REDIS_APPLICATION_PASSWORD est requise.}"

umask 077
printf '%s\n' \
    'user default off' \
    "user application on >${REDIS_APPLICATION_PASSWORD} ~* +@all" \
    > /run/redis/users.acl

exec redis-server /usr/local/etc/redis/redis.conf