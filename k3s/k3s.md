# De Podman Compose à k3s

Exécuter les commandes depuis la racine du dépôt. `sudo k3s kubectl` est utilisé ici car le kubeconfig local n'est pas lisible sans privilèges. Toutes les ressources applicatives sont dans le namespace `demo-project` ; les Pods système de k3s restent indépendants.

| Compose | k3s |
| --- | --- |
| `podman compose up` | Installer les manifests, puis démarrer les contrôleurs (voir ci-dessous). |
| `podman compose logs <service>` | `sudo k3s kubectl -n demo-project logs deployment/<service> --all-pods=true` |
| `podman compose logs <service> -f` | `sudo k3s kubectl -n demo-project logs -f deployment/<service> --all-pods=true` |
| `podman compose up -d --force-recreate` | `sudo k3s kubectl -n demo-project rollout restart deployment/<service>` |
| `podman compose down <service>` | Mettre le contrôleur de ce service à zéro réplique. |
| `podman compose down` | Mettre à zéro tous les contrôleurs du projet, sans toucher aux volumes. |
| `podman compose down -v` | Arrêter le projet, puis supprimer explicitement ses PVC : **données perdues**. |

Pour PostgreSQL, remplacer `deployment/<service>` par `statefulset/postgres`. Pour les tâches ponctuelles, utiliser `logs job/emsc-migrations` ou `logs job/emsc-seed` ; elles ne sont pas lancées avec les services permanents. Les noms des autres Deployments sont `api-back`, `api-front`, `api-worker`, `api-collect` et `redis`.

## Installer et démarrer (`up`)

Une installation initiale nécessite des images déjà publiées et les vrais fichiers `secret.yaml` préparés hors des exemples. Ne pas faire `apply -R -f k3s/` : cela mélangerait services et Jobs, sans garantir l'ordre des dépendances. Appliquer d'abord les ressources communes, les volumes et les Services :

```bash
sudo k3s kubectl apply -f k3s/namespace.yaml
sudo k3s kubectl apply \
  -f k3s/postgres/configmap.yaml -f k3s/postgres/secret.yaml \
  -f k3s/postgres/pvc.yaml -f k3s/postgres/service.yaml \
  -f k3s/redis/secret.yaml -f k3s/redis/pvc.yaml -f k3s/redis/service.yaml \
  -f k3s/configmap-common.yaml -f k3s/secret-common.yaml \
  -f k3s/api-front/configmap.yaml -f k3s/api-front/secret.yaml \
  -f k3s/api-worker/configmap.yaml \
  -f k3s/api-back/service.yaml -f k3s/api-front/service.yaml \
  -f k3s/api-front/ingress.yaml
```

Créer les contrôleurs dans l'ordre des dépendances. Attendre que PostgreSQL accepte réellement les connexions avant les API ; sa readiness probe utilise `pg_isready`.

```bash
sudo k3s kubectl apply -f k3s/postgres/deployment.yaml
sudo k3s kubectl -n demo-project scale statefulset/postgres --replicas=1
sudo k3s kubectl -n demo-project rollout status statefulset/postgres --timeout=300s

sudo k3s kubectl apply -f k3s/redis/deployment.yaml
sudo k3s kubectl -n demo-project scale deployment/redis --replicas=1
sudo k3s kubectl -n demo-project rollout status deployment/redis --timeout=180s

sudo k3s kubectl apply \
  -f k3s/api-back/deployment.yaml -f k3s/api-front/deployment.yaml \
  -f k3s/api-worker/deployment.yaml -f k3s/api-collect/deployment.yaml
sudo k3s kubectl -n demo-project scale deployment/api-back deployment/api-front --replicas=2
sudo k3s kubectl -n demo-project scale deployment/api-worker deployment/api-collect --replicas=1
sudo k3s kubectl apply -f k3s/api-back/hpa.yaml -f k3s/api-front/hpa.yaml
sudo k3s kubectl -n demo-project get deployments,statefulsets,pods
```

Après un arrêt, les contrôleurs, Services, ConfigMaps, Secrets, Ingress et PVC existent encore : reprendre à `scale statefulset/postgres --replicas=1`, puis suivre le même ordre Redis → applications → HPA. `kubectl apply` ne garantit pas à lui seul le retour au nombre de répliques souhaité après un `scale` manuel.

## Logs et redémarrage (`logs`, `up -d --force-recreate`)

```bash
sudo k3s kubectl -n demo-project logs deployment/api-front --all-pods=true
sudo k3s kubectl -n demo-project logs -f deployment/api-front --all-pods=true
sudo k3s kubectl -n demo-project logs statefulset/postgres

sudo k3s kubectl -n demo-project rollout restart deployment/api-front
sudo k3s kubectl -n demo-project rollout status deployment/api-front --timeout=180s

# Pour recréer tous les services permanents déjà installés :
sudo k3s kubectl -n demo-project rollout restart deployment
sudo k3s kubectl -n demo-project rollout restart statefulset/postgres
```

`rollout restart` recrée les Pods d'un contrôleur actif, mais ne reconstruit ni ne publie l'image. Pour une nouvelle image, la publier avec un nouveau tag, mettre ce tag dans le manifeste, puis l'appliquer. Un contrôleur à zéro réplique reste à zéro après un `rollout restart`.

## Arrêter un service (`down <service>`)

```bash
# Exemple : api-front est piloté par un HPA ; le retirer avant de le mettre à zéro.
sudo k3s kubectl -n demo-project delete hpa api-front --ignore-not-found
sudo k3s kubectl -n demo-project scale deployment/api-front --replicas=0

# PostgreSQL est un StatefulSet, pas un Deployment.
sudo k3s kubectl -n demo-project scale statefulset/postgres --replicas=0
```

La commande `podman compose down <service>` n'a pas d'équivalent direct : ici, le Service Kubernetes reste défini, mais sans Pod disponible. Pour relancer `api-front`, lui rendre ses 2 répliques, puis réappliquer `k3s/api-front/hpa.yaml`.

## Arrêter le projet (`down`)

```bash
sudo k3s kubectl -n demo-project delete hpa api-back api-front --ignore-not-found
sudo k3s kubectl -n demo-project scale deployment/api-back deployment/api-front \
  deployment/api-worker deployment/api-collect --replicas=0
sudo k3s kubectl -n demo-project scale deployment/redis --replicas=0
sudo k3s kubectl -n demo-project scale statefulset/postgres --replicas=0
sudo k3s kubectl -n demo-project get pods
```

Ces commandes supposent que tous les contrôleurs cités ont été installés. Si certains n'existent pas encore, vérifier `get deployments,statefulsets` et ne citer que ceux présents, ou utiliser `scale deployment,statefulset --all --replicas=0` après la suppression des HPA (sans ordre d'arrêt garanti). Les Pods des Jobs terminés peuvent encore apparaître comme `Completed` : supprimer ces Jobs seulement après conservation des logs utiles. Ne pas utiliser `delete pods --all` : les contrôleurs recréeraient leurs Pods.

## Supprimer aussi les données (`down -v`)

**Irréversible :** une fois les contrôleurs arrêtés et leurs Pods disparus, supprimer les PVC efface les données PostgreSQL et Redis avec le provisionneur `local-path`. Les migrations et le seed devront être relancés sur de nouveaux volumes.

```bash
sudo k3s kubectl -n demo-project get pods,pvc
# Après vérification qu'aucun Pod du projet n'utilise ces volumes :
sudo k3s kubectl -n demo-project delete pvc postgres-data redis-data
```

Ne pas supprimer le namespace pour un simple arrêt : cela retirerait aussi les Services, Ingress, ConfigMaps et Secrets. Les PVC sont conservés par `down` et par `down <service>`.
