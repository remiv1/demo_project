#!/bin/bash

set -euo pipefail

seed_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "$seed_dir/../.." && pwd)"
environment_file="$project_root/src/database/.env.postgres"
network="${SEED_NETWORK:-demo_project_default}"
image="emsc-seed"
registry_image="ghcr.io/remiv1/emsc-seed"

build_image() {
    podman build \
        --build-arg "APP_UID=${APP_UID:-$(id -u)}" \
        --build-arg "APP_GID=${APP_GID:-$(id -g)}" \
        -f "$seed_dir/Dockerfile" \
        -t "$1" \
        "$project_root"
}

if [[ "$#" -gt 0 ]]; then
    [[ "$#" -eq 1 && "$1" == --push-image ]] \
        || { echo "Usage : $0 [--push-image]" >&2; exit 1; }
    tag="${IMAGE_TAG:-}"
    [[ "$tag" =~ ^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$ ]] \
        || { echo "IMAGE_TAG doit contenir un tag d'image valide." >&2; exit 1; }
    target_image="$registry_image:$tag"
    build_image "$target_image"
    podman push "$target_image"
    exit 0
fi

if [[ ! -f "$environment_file" || ! -f "$seed_dir/infra.conf" ]]; then
    echo "Fichier d'environnement PostgreSQL ou configuration d'ingestion absent." >&2
    exit 1
fi

if ! podman network inspect "$network" >/dev/null 2>&1; then
    echo "Réseau $network absent : démarrer PostgreSQL avec podman compose avant l'import." >&2
    exit 1
fi

build_image "$image"

run_args=(
    --rm
    --network "$network"
    --env-file "$environment_file"
    --env POSTGRES_HOST=postgres
    --volume "$seed_dir/infra.conf:/app/infra.conf:ro,z"
)

if [[ -n "${HISTORY_START:-}" ]]; then
    run_args+=(--env "HISTORY_START=$HISTORY_START")
fi
if [[ -n "${HISTORY_END:-}" ]]; then
    run_args+=(--env "HISTORY_END=$HISTORY_END")
fi

podman run "${run_args[@]}" "$image"