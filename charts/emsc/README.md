# Déployer EMSC avec Helm

Ce document a pour objectif de rendre le déploiement de l'application plus simple à comprendre, même pour une personne qui n'est pas très à l'aise avec Kubernetes ou les conteneurs.

L'idée principale : Helm sert à dire à Kubernetes : "voici les services que je veux, sous quel nom, avec quelles données et quelles règles de fonctionnement". Sans cela, il faudrait écrire beaucoup de fichiers de configuration manuellement.

## 1. À quoi sert ce projet ?

EMSC est une application composée de plusieurs éléments qui travaillent ensemble :

- une base de données PostgreSQL pour stocker les données structurées,
- Redis pour les files d'attente (gestion du temps réel) et les événements rapides,
- un collecteur pour récupérer les événements externes et les mettre dans le flux de traitement,
- un worker pour traiter les tâches asynchrones et les messages en arrière-plan,
- une API backend pour le traitement métier,
- une interface frontend pour l'usage humain,
- des tâches de migration et d'initialisation de données.

En pratique, le chart Helm regroupe ces briques dans un même paquet de déploiement. Il permet de lancer, configurer et remettre en service l'application de manière répétable.

---

## 2. Le point de départ : ce que contient le chart

Le dossier `charts/emsc` contient les fichiers de configuration du déploiement. Voici le rôle de chacun :

- `Chart.yaml` : identifie le chart et sa version.
- `values.yaml` : contient les réglages par défaut.
- `templates/` : contient les fichiers Kubernetes réels que Helm va générer.
- `secrets/` : contient les fichiers de secrets sensibles et leurs exemples.

En langage simple :

- `values.yaml` dit : "je veux 1 base de données, un Redis, 2 API, etc."
- `templates/` dit : "voilà la forme exacte des objets Kubernetes à créer".
- Helm combine les deux pour produire des fichiers prêts à être envoyés à Kubernetes.

> Le namespace n'est pas inscrit en dur dans les fichiers. Il est donné avec la commande `--namespace`.

---

## 3. La logique sans jargon : les composants clés

### Les services permanents

Ce sont les éléments qui doivent rester actifs tout le temps :

- PostgreSQL
- Redis
- le collecteur de données externes
- le worker de traitement asynchrone
- le backend API
- le frontend API
- les règles de mise à l'échelle (HPA)
- les points d'entrée réseau (Service, Ingress)

Ces composants sont activés par défaut lors d'un déploiement normal.

> Une mise à l'échelle automatique (HPA) permet d'ajuster le nombre d'ouvriers en fonction de la charge de travail.

### Les tâches spéciales

Les migrations et le seed ne sont pas des services "normaux". Ce sont des actions ponctuelles :

- une migration met à jour la structure de la base de données,
- un seed charge des données initiales ou historiques,
- le collecteur et le worker restent actifs pour alimenter et traiter les flux en continu.

Ils sont désactivés par défaut pour éviter de les relancer involontairement à chaque mise à jour.

---

## 4. Les volumes de stockage : pourquoi cela compte

Les volumes de stockage, ou PVC (Persistent Volume Claim), servent à garder les données même si le conteneur est relancé ou redémarré.

Sans stockage persistant :

- la base PostgreSQL perdrait ses données,
- Redis perdrait son état,
- les données importées ne seraient plus disponibles après redémarrage.

### Deux cas possibles

1. Créer les volumes automatiquement via Helm
   - c'est la solution la plus simple,
   - Helm demande les volumes pour vous,
   - par défaut, les tailles sont prévues pour un usage standard.

2. Reutiliser des volumes déjà existants
   - on crée le PVC en dehors du chart,
   - on indique son nom dans `existingClaim`,
   - Helm monte simplement ce volume sans le recréer.

Exemple de configuration de surcharge :

```yaml
postgres:
  persistence:
    size: 20Gi

redis:
  persistence:
    existingClaim: redis-data-externe
```

### À retenir (Volumes)

- `local-path` est la classe de stockage de k3s sur une machine locale.
- `helm.sh/resource-policy: keep` permet de conserver les volumes même après une suppression du chart.
- cela n'est pas une sauvegarde automatique,
- il faut sauvegarder les données avant une suppression définitive.

---

## 5. Les secrets : gardons les mots de passe hors du code

Les secrets contiennent des informations sensibles comme :

- clés d'authentification,
- mots de passe,
- tokens,
- clés de chiffrement.

Il ne faut pas les laisser dans un fichier Git, dans un paquet Helm ou dans l'historique de la release.

Le principe de ce chart est simple :

- les fichiers réels de secrets sont stockés localement et non versionnés,
- les fichiers `.example` restent visibles pour montrer le format attendu,
- Helm ne crée pas ces secrets directement dans le dépôt.

Les vrais fichiers sont généralement stockés dans `charts/emsc/secrets/` et ignorés par Git. Les exemples servent de modèle.

### Exemple de création des secrets

```bash
sudo k3s kubectl create namespace demo-project --dry-run=client -o yaml | sudo k3s kubectl apply -f -
sudo k3s kubectl apply \
  -f charts/emsc/secrets/secret-common.yaml \
  -f charts/emsc/secrets/postgres/secret.yaml \
  -f charts/emsc/secrets/redis/secret.yaml \
  -f charts/emsc/secrets/api-front/secret.yaml
```

### À retenir (Secrets)

- ne pas copier directement les fichiers d'exemple sans les compléter,
- remplacer les valeurs par de vraies clés et mots de passe,
- utiliser le même namespace que la release,
- vérifier les secrets avant un déploiement important.

---

## 6. Déployer l'application

Avant de lancer le chart, il faut vérifier que les images sont bien disponibles. Si les images sont privées, il faut aussi créer un secret d'accès au registre et le déclarer dans `values.yaml`.

Si vous voulez utiliser des images personnalisées de conteneurs, vous devez les spécifier dans le fichier `values.yaml` pour chaque composant concerné et compiler de nouvelles images à partir de podman compose avant de déployer le chart.

### Vérification locale du chart

```bash
helm lint charts/emsc
helm template emsc charts/emsc --namespace demo-project
```

Ces commandes ne déploient rien ; elles vérifient la syntaxe et le rendu final du chart.

### Installation réelle

```bash
sudo helm upgrade --install emsc ./charts/emsc \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  --namespace demo-project --create-namespace \
  --wait --timeout 10m
```

Puis on vérifie l'état des ressources :

```bash
sudo k3s kubectl -n demo-project get pods,pvc,ingress
```

### Que se passe-t-il pendant l'installation ?

Kubernetes va créer les objets demandés :

- un ou plusieurs pods pour chaque service,
- les services réseau,
- les objets d'entrée HTTP,
- les volumes de stockage,
- les variables d'environnement nécessaires.

`--wait` permet d'attendre jusqu'à ce que les composants soient prêts, selon leurs probes de santé. Cela ne remplace pas la migration de base de données si la base est neuve.

---

## 7. L'Ingress : comment le monde accède à l'application

L'Ingress est la porte d'entrée publique de l'application. Dans le contexte du projet, il pointe sur un domaine de type :

```text
emsc.testing.audit-io.fr
```

Cela signifie que les requêtes web arrivent sur ce nom de domaine et sont envoyées vers le bon service interne.

Le certificat HTTPS peut être géré par un proxy ou une configuration externe. Le chart ne crée pas forcément le certificat lui-même.

---

## 8. Migration et chargement des données initiales

Quand on installe une application pour la première fois, il faut souvent faire deux opérations distinctes :

1. mettre à jour la structure de la base,
2. remplir la base avec des données de départ.

### Migration

La migration sert à préparer la base de données pour la version actuelle de l'application.

```bash
helm template emsc charts/emsc --namespace demo-project \
  --set migration.enabled=true --show-only templates/migration/job.yaml \
  | sudo k3s kubectl create -f -

sudo k3s kubectl -n demo-project wait --for=condition=complete job/emsc-migrations --timeout=10m
sudo k3s kubectl -n demo-project logs job/emsc-migrations
```

### Seed

Le seed sert à importer des données historiques ou de référence.

```bash
helm template emsc charts/emsc --namespace demo-project \
  --set seed.enabled=true --show-only templates/seed/configmap.yaml \
  | sudo k3s kubectl apply -f -

helm template emsc charts/emsc --namespace demo-project \
  --set seed.enabled=true --show-only templates/seed/job.yaml \
  | sudo k3s kubectl create -f -

sudo k3s kubectl -n demo-project logs -f job/emsc-seed
sudo k3s kubectl -n demo-project wait --for=condition=complete job/emsc-seed --timeout=24h
```

### À retenir

- les migrations et le seed sont des tâches ponctuelles,
- ne pas les relancer sans raison,
- ne pas exécuter deux migrations en même temps,
- conserver les logs avant de recommencer.

---

## 9. Mettre l'application en veille

La veille est utile quand on ne veut pas supprimer tout, mais qu'on veut arrêter de servir l'application temporairement.

```bash
sudo helm upgrade emsc ./charts/emsc \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  --namespace demo-project --set suspended=true --wait --timeout 10m
```

Cela met les contrôleurs principaux en sommeil, tout en conservant :

- les services réseau,
- l'Ingress,
- les secrets,
- les volumes persistants.

### Pour réveiller l'application

```bash
sudo helm upgrade emsc ./charts/emsc \
  --kubeconfig /etc/rancher/k3s/k3s.yaml \
  --namespace demo-project --set suspended=false --wait --timeout 10m
```

> La veille ne relance pas automatiquement les migrations ni le seed.

---

## 10. Désinstaller ou nettoyer complètement

### Désinstaller le chart

```bash
sudo helm uninstall emsc --namespace demo-project \
  --kubeconfig /etc/rancher/k3s/k3s.yaml --wait
```

### Que se passe-t-il alors ?

- les objets Helm sont retirés,
- les secrets externes peuvent rester,
- les PVC conservés peuvent rester également,
- cela dépend de leur politique de conservation.

### Suppression totale

La suppression du namespace efface aussi les ressources associées, y compris les données de volumes `local-path` dans certains cas. C'est une étape irréversible.

Avant de supprimer complètement, il faut sauvegarder les données si elles sont importantes.

---

## 11. Checklist simple pour une première installation

Si vous êtes débutant, voici la séquence la plus sûre :

1. Vérifier que le cluster k3s est accessible.
2. Créer le namespace.
3. Appliquer les secrets sensibles.
4. Vérifier les valeurs dans `values.yaml`.
5. Lancer `helm lint` puis `helm template`.
6. Installer le chart avec `helm upgrade --install`.
7. Vérifier les pods et le service réseau.
8. Exécuter la migration si nécessaire.
9. Exécuter le seed si c'est une base neuve.
10. Tester l'accès web via le domaine configuré.

---

## 12. Conseils pratiques

- Garder les secrets hors du dépôt Git.
- Ne pas modifier directement les fichiers versionnés pour des valeurs sensibles.
- Conserver un fichier de surcharge YAML si vous personnalisez la taille du stockage ou les images.
- Vérifier les logs des jobs avant de les relancer.
- Ne pas effacer un volume sans vérifier qu'il ne contient pas de données utiles.

Ce chart est conçu pour être prévisible et reproductible. Une installation bien préparée est beaucoup plus simple à surveiller et à remettre en état en cas de problème.

---

## 13. En résumé

Helm est ici un outil de déploiement qui rend la mise en place de l'application plus claire et plus fiable. Il ne remplace pas la compréhension du système, mais il aide à organiser les composants, les données et les secrets de manière plus sûre.

Pour une personne non technique, il faut surtout retenir cette idée :

- le chart décrit le système,
- les secrets gardent les mots de passe hors du code,
- les volumes gardent les données,
- les jobs servent à lancer des actions ponctuelles comme la migration ou le chargement initial.

Si vous suivez cette logique, le déploiement devient beaucoup plus lisible et moins intimidant.
