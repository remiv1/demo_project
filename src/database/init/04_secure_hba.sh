#!/bin/bash

set -euo pipefail

hba="$PGDATA/pg_hba.conf"
sed -i '/^[[:space:]]*local[[:space:]]\+all[[:space:]]\+all[[:space:]]\+trust/d' "$hba"
sed -i '/^[[:space:]]*host[[:space:]]\+all[[:space:]]\+all[[:space:]]\+.*trust/d' "$hba"
sed -i '/^[[:space:]]*local[[:space:]]\+all[[:space:]]\+all[[:space:]]\+ident/d' "$hba"

grep -q '^local[[:space:]]\+all[[:space:]]\+all' "$hba" \
    || echo 'local   all   all   scram-sha-256' >> "$hba"
grep -q 'host.*scram-sha-256' "$hba" \
    || echo 'host    all   all   0.0.0.0/0   scram-sha-256' >> "$hba"