# Guide de migration Podman Compose → k3s

## Installer Kompose sur Fedora

```bash
curl -L https://github.com/kubernetes/kompose/releases/latest/download/kompose-linux-amd64 \
-o kompose
chmod +x kompose
sudo mv kompose /usr/local/bin/
```

Vérification :

```bash
kompose version
```

## Utiliser Kompose

À partir d'un fichier :

```bash
kompose convert -f docker-compose.yaml
```

Ou générer les fichiers dans un dossier :

```bash
mkdir k8s
kompose convert \
-f docker-compose.yaml \
--out k8s
```

Résultat typique :

```text
k8s/
├── postgres-deployment.yaml
├── postgres-service.yaml
├── postgres-persistentvolumeclaim.yaml
├── redis-deployment.yaml
├── redis-service.yaml
├── redis-persistentvolumeclaim.yaml
├── app-deployment.yaml
├── app-service.yaml
├── configmap.yaml
```

## Modifications à réaliser après Kompose

### Déplacer les mots de passe hors des ConfigMaps

- Mauvais

    ```yaml
    kind: ConfigMap
    data:
    POSTGRES_PASSWORD: secret
    ```

- Bon

    ```yaml
    kind: Secret

    # ou

    envFrom:
    - secretRef:
        name: postgres-secret
    ```

### Augmenter les volumes persistants

Kompose génère souvent :

```yaml
storage: 100Mi
```

À remplacer par :

```yaml
storage: 10Gi

# ou

storage: 20Gi
```

pour PostgreSQL.

### Ajouter les images correctes

Kompose conserve parfois :

```yaml
image: postgres
image: redis
```

ou des images locales :

```yaml
image: localhost/demo_project_postgres
```

À remplacer par :

```yaml
image: registry.local/demo_project_postgres:latest
```

ou une image Docker Hub officielle.

### Créer un Service pour chaque composant

Pour PostgreSQL :

```yaml
kind: Service
metadata:
  name: postgres
```

Pour Redis :

```yaml
kind: Service
metadata:
  name: redis
```

Les applications pourront alors utiliser :

```text
postgres:5432
redis:6379
```

### Créer des Secrets depuis un fichier .env

Fichier secret.env

```conf
POSTGRES_PASSWORD=motdepasse
POSTGRES_PASSWORD_APP=motdepasseapp
POSTGRES_PASSWORD_MIGR=motdepassemigr

REDIS_APPLICATION_PASSWORD=monredispass
```

Création du Secret :

```bash
kubectl create secret generic app-secret \
--from-env-file=secret.env
```

Vérification :

```bash
kubectl get secrets
```

### Utiliser les Secrets dans les fichiers YAML

#### Injection complète

```yaml
envFrom:
  - secretRef:
    name: app-secret
```

Toutes les variables du Secret seront disponibles.

#### Injection variable par variable

```yaml
env:
  - name: POSTGRES_PASSWORD
    valueFrom:
      secretKeyRef:
        name: app-secret
        key: POSTGRES_PASSWORD
```

### Utiliser ConfigMaps pour les variables non sensibles

Fichier app.env

```conf
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_HOST=postgres
```

Création :

```bash
kubectl create configmap app-config \
--from-env-file=app.env
```

Dans le Deployment :

```yaml
envFrom:
  - configMapRef:
      name: app-config
```

### Déployer les ressources

Tout déployer :

```bash
kubectl apply -f .
```

Vérifier :

```bash
kubectl get all
```

### Vérifications utiles

Afficher les Pods

```bash
kubectl get pods
```

Afficher les Services

```bash
kubectl get svc
```

Afficher les PVC

```bash
kubectl get pvc
```

Afficher les logs PostegreSQL

```bash
kubectl logs -f deployment/postgres
```

Afficher les logs Redis

```bash
kubectl logs -f deployment/redis
```

### Arborescence recommandée

```txt
k8s/
├── config/
│ ├── app.env
│ └── postgres.env
│
├── secrets/
│ └── secret.env
│
├── postgres/
│ ├── pvc.yaml
│ ├── deployment.yaml
│ └── service.yaml
│
├── redis/
│ ├── pvc.yaml
│ ├── deployment.yaml
│ └── service.yaml
│
├── fastapi/
│ ├── deployment.yaml
│ └── service.yaml
│
├── flask/
│ ├── deployment.yaml
│ └── service.yaml
│
└── ingress/
  └── ingress.yaml
```

### Cas particulier du projet

On a déjà :

✅ PostgreSQL Deployment
 ✅ Redis Deployment
 ✅ PostgreSQL PVC
 ✅ Redis PVC
 ✅ ConfigMaps générées automatiquement

Il reste principalement à :

- Remplacer les ConfigMaps contenant des mots de passe par des Secrets.
- Augmenter les tailles des PVC.
- Vérifier les images Docker utilisées.
- Ajouter les Services PostgreSQL et Redis si Kompose ne les a pas générés.
- Ajouter ensuite FastAPI et Flask.
- Créer un Ingress Traefik pour exposer les applications web.

Il y a déjà environ 80 % de la migration vers k3s

## Notes supplémentaires

### A quoi correspondent les différents fichiers ?

| Fichier         | Question                                |
| --------------- | --------------------------------------- |
| pvc.yaml        | Où stocker les données ?                |
| deployment.yaml | Quel conteneur exécuter ?               |
| service.yaml    | Comment les autres pods le contactent ? |
| configmap.yaml  | Quelles variables non sensibles ?       |
| secret.yaml     | Quels mots de passe et clés ?           |
