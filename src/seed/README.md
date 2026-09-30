# Génération du jeu de données initial

Pour générer le jeu de données initial, paramétrez la date de départ dans le fichier `infra.conf`.

```toml
[ingestion]
history_start = "2024-01-01T00:00:00Z"
timeout = 30
```

Ensuite, exécutez le script d'importation des données qui construira le conteneur et importera les données initiales :

```bash
./src/seed/run-seed.sh
```

## Cas d'utilisation avec kubernetes

Pour exporter une image dans un registre GH/Docker, utilisez la commande suivante :

```bash
IMAGE_TAG=x.x.x ./src/seed/run-seed.sh --push-image
```

Enfin pour déployer le jeu de données initial dans un cluster Kubernetes, utilisez le job Kubernetes approprié ou un manifeste YAML configuré pour exécuter le script de seed.
