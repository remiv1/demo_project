# Migrations de emsc

Un environnement Alembic indépendant est généré pour chaque base configurée.

```bash
./src/migration/run-migrations.sh --generate
./src/migration/run-migrations.sh --run-dry
./src/migration/run-migrations.sh --apply
```

Les chemins `metadata` et `model_modules` de la configuration TOML déterminent les modèles chargés pour l'autogénération.

## Cas d'utilisation avec kubernetes

Pour créer une nouvelle image et l'envoyer vers un registre GH/Docker, utilisez les commandes suivantes :

```bash
IMAGE_TAG=x.x.x ./src/migration/run-migrations.sh --push-image
```

Enfin pour déployer les migrations dans un cluster Kubernetes, utilisez le job Kubernetes approprié ou un manifeste YAML configuré pour exécuter les migrations.
