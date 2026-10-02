#!/usr/bin/env bash
set -euo pipefail

chart_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
namespace="demo-project"
release="emsc"
kubeconfig="/etc/rancher/k3s/k3s.yaml"
privilege=()
if (( EUID != 0 )); then
  privilege=(sudo)
fi

usage() {
  printf '%s\n' \
    'Usage : bash charts/emsc/deploy.sh ACTION [-f fichier.yaml ...]' \
    '  --up              Appliquer les Secrets, installer ou réveiller EMSC.' \
    '  --down            Mettre en veille sans supprimer les données.' \
    '  --logs SERVICE    Suivre les logs de toutes les répliques.' \
    '  --migr            Créer le Job de migration et attendre sa réussite.' \
    '  --seed            Créer le Job de seed et attendre sa réussite.' \
    '  --help            Afficher cette aide.' \
    'Services : api-back, api-front, api-collect, api-worker, postgres, redis,' \
    '           migration, seed.' \
    'Namespace : demo-project ; release : emsc.' \
    'Réutiliser les mêmes fichiers -f pour chaque action.' \
    'Les Jobs existants ne sont jamais supprimés automatiquement.'
}

fail() {
  printf 'Erreur : %s\n' "$*" >&2
  exit 1
}

kubectl_cmd() {
  "${privilege[@]}" k3s kubectl --kubeconfig "$kubeconfig" -n "$namespace" "$@"
}

helm_cmd() {
  "${privilege[@]}" helm "$@" --kubeconfig "$kubeconfig" --namespace "$namespace"
}

action="${1:---help}"
shift "$(( $# > 0 ? 1 : 0 ))"
service=""
case "$action" in
  --help) usage; exit 0 ;;
  --logs)
    (( $# > 0 )) || fail 'Indiquer un service après --logs.'
    service="$1"
    shift
    case "$service" in
      api-back|api-front|api-collect|api-worker|postgres|redis|migration|seed) ;;
      *) fail "Service inconnu : $service." ;;
    esac
    ;;
  --up|--down|--migr|--seed) ;;
  *) usage >&2; fail "Action inconnue : $action." ;;
esac

values_args=()
while (( $# > 0 )); do
  case "$1" in
    -f|--values)
      (( $# >= 2 )) || fail 'Indiquer un fichier après -f.'
      [[ -r "$2" ]] || fail "Fichier illisible : $2."
      values_args+=(-f "$2")
      shift 2
      ;;
    *) fail "Argument inconnu : $1." ;;
  esac
done
[[ "$action" != --logs || ${#values_args[@]} == 0 ]] || fail '--logs ne prend pas de fichier de valeurs.'

command -v k3s >/dev/null || fail 'k3s est introuvable.'
if [[ "$action" != --logs ]]; then
  command -v helm >/dev/null || fail 'Helm est introuvable.'
fi

case "$action" in
  --up)
    secret_files=(
      "$chart_dir/secrets/secret-common.yaml"
      "$chart_dir/secrets/postgres/secret.yaml"
      "$chart_dir/secrets/redis/secret.yaml"
      "$chart_dir/secrets/api-front/secret.yaml"
    )
    secret_args=()
    for secret_file in "${secret_files[@]}"; do
      [[ -r "$secret_file" ]] || fail "Secret privé manquant ou illisible : $secret_file. Compléter son exemple avant de continuer."
      secret_args+=(-f "$secret_file")
    done
    kubectl_cmd create namespace "$namespace" --dry-run=client -o yaml | kubectl_cmd apply -f -
    kubectl_cmd apply "${secret_args[@]}"
    reuse_args=()
    existing_release="$(helm_cmd list --filter '^emsc$' -q)" || fail 'Impossible de consulter les releases Helm.'
    if [[ -n "$existing_release" ]]; then
      reuse_args=(--reuse-values)
    fi
    helm_cmd upgrade --install "$release" "$chart_dir" \
      "${reuse_args[@]}" "${values_args[@]}" \
      --set suspended=false --set migration.enabled=false --set seed.enabled=false \
      --server-side=false --wait --timeout 10m
    kubectl_cmd get pods,pvc,ingress
    ;;
  --down)
    active_jobs="$(kubectl_cmd get jobs -o jsonpath='{range .items[*]}{.status.active}{"\n"}{end}')"
    while IFS= read -r active_count; do
      [[ ! "$active_count" =~ ^[1-9][0-9]*$ ]] || fail 'Un Job est encore actif. Attendre sa fin avant la veille.'
    done <<< "$active_jobs"
    helm_cmd upgrade "$release" "$chart_dir" --reuse-values "${values_args[@]}" \
      --set suspended=true --set migration.enabled=false --set seed.enabled=false \
      --server-side=false --wait --timeout 10m
    kubectl_cmd wait --for=delete pods \
      -l 'app in (api-back,api-front,api-collect,api-worker,postgres,redis)' --timeout=10m
    ;;
  --logs)
    case "$service" in
      migration) kubectl_cmd logs -f job/emsc-migrations --tail=100 --timestamps=true ;;
      seed) kubectl_cmd logs -f job/emsc-seed --tail=100 --timestamps=true ;;
      *) kubectl_cmd logs -f -l "app=$service" --all-containers=true \
           --max-log-requests=20 --prefix=true --tail=100 --timestamps=true ;;
    esac
    ;;
  --migr|--seed)
    if [[ "$action" == --migr ]]; then
      job_name="emsc-migrations"
      job_template="templates/migration/job.yaml"
      enabled_value="migration.enabled=true"
      job_timeout="10m"
      log_service="migration"
    else
      job_name="emsc-seed"
      job_template="templates/seed/job.yaml"
      enabled_value="seed.enabled=true"
      job_timeout="24h"
      log_service="seed"
      kubectl_cmd wait --for=condition=complete job/emsc-migrations --timeout=10m
    fi
    existing_job="$(kubectl_cmd get job "$job_name" --ignore-not-found -o name)"
    [[ -z "$existing_job" ]] || fail "Le Job $job_name existe déjà. Consulter ses logs puis le supprimer explicitement avant une nouvelle exécution."
    kubectl_cmd rollout status statefulset/postgres --timeout=10m
    work_dir="$(mktemp -d)"
    trap 'rm -rf -- "$work_dir"' EXIT
    helm_cmd get values "$release" -o yaml > "$work_dir/values.yaml"
    render_args=(-f "$work_dir/values.yaml" "${values_args[@]}" --set suspended=false --set "$enabled_value")
    if [[ "$action" == --seed ]]; then
      helm template "$release" "$chart_dir" --namespace "$namespace" \
        "${render_args[@]}" --show-only templates/seed/configmap.yaml > "$work_dir/configmap.yaml"
    fi
    helm template "$release" "$chart_dir" --namespace "$namespace" \
      "${render_args[@]}" --show-only "$job_template" > "$work_dir/job.yaml"
    if [[ "$action" == --seed ]]; then
      kubectl_cmd apply -f "$work_dir/configmap.yaml"
    fi
    kubectl_cmd create -f "$work_dir/job.yaml"
    printf 'Suivre les logs dans un autre terminal avec --logs %s.\n' "$log_service"
    if kubectl_cmd wait --for=condition=complete "job/$job_name" --timeout="$job_timeout"; then
      kubectl_cmd logs "job/$job_name" --tail=100
    else
      kubectl_cmd logs "job/$job_name" --tail=100 || true
      fail "Le Job $job_name n'a pas terminé avec succès dans le délai prévu."
    fi
    ;;
esac