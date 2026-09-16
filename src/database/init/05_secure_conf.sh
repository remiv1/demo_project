#!/bin/bash

set -euo pipefail

configuration="$PGDATA/postgresql.conf"
sed -i "s/^#\?password_encryption.*/password_encryption = 'scram-sha-256'/" "$configuration"