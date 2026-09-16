# Migrations de emsc

Un environnement Alembic indépendant est généré pour chaque base configurée.

```bash
./src/migration/run-migrations.sh --generate
./src/migration/run-migrations.sh --run-dry
./src/migration/run-migrations.sh --apply
```

Les chemins `metadata` et `model_modules` de la configuration TOML déterminent les modèles chargés pour l'autogénération.