#!/bin/bash

set -euo pipefail

project_name="demo_project"
container_engine="podman"
network="${project_name}_emsc-migrations"
image="emsc-migrations"
container_root="/app"
host_project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
environment_file="$host_project_root/migration/.env.migr"
databases=("main" "users" )

usage() {
    echo "Usage : $0 (--generate|--run-dry|--apply) [--force-recreate]"
}

select_databases() {
    local selection
    PS3="Bases à traiter : "
    select selection in "${databases[@]}" "toutes" "annuler"; do
        if [[ "$selection" == "toutes" ]]; then
            selected_databases=("${databases[@]}")
            return
        fi
        if [[ "$selection" == "annuler" ]]; then
            exit 0
        fi
        if [[ -n "$selection" ]]; then
            selected_databases=("$selection")
            return
        fi
        echo "Sélection invalide."
    done
}

configure_database() {
    local database_id="$1"
    migration_dir="$container_root/$database_id"
    host_migration_dir="$host_project_root/migration/$database_id"
}

check_prerequisites() {
    [[ -f "$environment_file" ]] || { echo "Fichier $environment_file absent." >&2; exit 1; }
    "$container_engine" network inspect "$network" >/dev/null 2>&1 \
        || { echo "Réseau $network absent." >&2; exit 1; }
    if [[ "$force_recreate" == true ]] || ! "$container_engine" image inspect "$image" >/dev/null 2>&1; then
        local build_args=()
        if [[ "$force_recreate" == true ]]; then
            build_args+=(--no-cache)
        fi
        "$container_engine" build \
            "${build_args[@]}" \
            -f "$host_project_root/migration/Dockerfile" \
            -t "$image" \
            "$host_project_root"
    fi
}

run_alembic() {
    local user_args=()
    if [[ "$1" == "revision" ]]; then
        if [[ "$("$container_engine" info --format '{{.Host.Security.Rootless}}')" != "true" ]]; then
            echo "La génération de migrations requiert Podman rootless." >&2
            exit 1
        fi
        user_args=(--user 0)
    fi
    "$container_engine" run --rm \
        "${user_args[@]}" \
        --network "$network" \
        --env-file "$environment_file" \
        -v "$host_migration_dir:$migration_dir:z" \
        -v "$host_project_root/common:/app/common:z" \
        "$image" \
        alembic -c "$migration_dir/alembic.ini" "$@"
}

generate_migration() {
    local migration_name
    read -r -p "Nom de la migration pour $1 : " migration_name
    [[ -n "$migration_name" ]] || { echo "Le nom est requis." >&2; exit 1; }
    run_alembic revision --autogenerate -m "$migration_name"
}

generate_dry_run() {
    local output_directory="$host_migration_dir/dry-runs"
    local output_file="$output_directory/$(date +%Y%m%d-%H%M%S)-upgrade-head.sql"
    mkdir -p "$output_directory"
    run_alembic upgrade head --sql > "$output_file"
    echo "SQL écrit dans $output_file."
}

apply_migrations() {
    local revision
    read -r -p "Révision cible [head] : " revision
    run_alembic upgrade "${revision:-head}"
}

action=""
force_recreate=false
for argument in "$@"; do
    case "$argument" in
        --generate|--run-dry|--apply)
            [[ -z "$action" ]] || { usage; exit 1; }
            action="$argument"
            ;;
        --force-recreate)
            [[ "$force_recreate" == false ]] || { usage; exit 1; }
            force_recreate=true
            ;;
        *) usage; exit 1 ;;
    esac
done
[[ -n "$action" ]] || { usage; exit 1; }
check_prerequisites
select_databases

for database_id in "${selected_databases[@]}"; do
    configure_database "$database_id"
    case "$action" in
        --generate) generate_migration "$database_id" ;;
        --run-dry) generate_dry_run ;;
        --apply) apply_migrations ;;
    esac
done