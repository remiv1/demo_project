#!/bin/sh

set -eu

umask 077
/usr/local/bin/generate-acl.sh --production

exec redis-server /usr/local/etc/redis/redis.conf