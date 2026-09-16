# Base de données emsc

Ce dossier contient l'image PostgreSQL 18 et les scripts exécutés lors de la première initialisation du volume.

## Construction

Depuis la racine du projet :

```bash
podman build -f src/database/Dockerfile -t emsc-postgres .
```

## Démarrage

```bash
podman run --rm \
  --name db-main \
  --env-file src/database/.env.postgres \
  emsc-postgres
```

Les fichiers `*.sql.pattern` sont substitués en mémoire au premier démarrage. Les secrets ne sont pas copiés dans l'image.


Les schémas de migration et le rôle migrateur sont créés parce que les migrations sont activées.
