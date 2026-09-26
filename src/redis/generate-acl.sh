#!/bin/sh

set -eu

ACTUAL_DIR=$(dirname "$0")

case "${1:-}" in
	--production)
		ACL_PATH="/run/redis/users.acl"
		;;
	--test)
		. "$ACTUAL_DIR/.env.redis"
		ACL_PATH="$ACTUAL_DIR/users.acl"
		;;
	*)
		echo "Usage : $0 --production|--test" >&2
		exit 1
		;;
esac

: "${REDIS_USERNAME:?La variable REDIS_USERNAME est requise.}"
: "${REDIS_PASSWORD:?La variable REDIS_PASSWORD est requise.}"
: "${REDIS_WORKER_USERNAME:?La variable REDIS_WORKER_USERNAME est requise.}"
: "${REDIS_WORKER_PASSWORD:?La variable REDIS_WORKER_PASSWORD est requise.}"
: "${REDIS_MONITOR_USERNAME:?La variable REDIS_MONITOR_USERNAME est requise.}"
: "${REDIS_MONITOR_PASSWORD:?La variable REDIS_MONITOR_PASSWORD est requise.}"

umask 077
cat > "$ACL_PATH" <<EOF

user default off

user ${REDIS_USERNAME} on >${REDIS_PASSWORD} ~* +xreadgroup +xack +xpending +ping
user ${REDIS_WORKER_USERNAME} on >${REDIS_WORKER_PASSWORD} ~* +xadd +xgroup +ping +exists +xinfo
user ${REDIS_MONITOR_USERNAME} on >${REDIS_MONITOR_PASSWORD} +@read
EOF
