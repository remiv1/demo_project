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

## Données géographiques et historique

L'image installe PostGIS 3 pour PostgreSQL 18. Le serveur s'exécute sous l'utilisateur
`postgres` (non-root) ; les paquets sont installés uniquement lors de la construction.
L'extension est activée au premier démarrage. La migration principale crée les tables
`app_schema.emsc`, `app_schema.emsc_details` et `app_schema.geographic_zone`.
Cette migration initiale a été alignée sur le modèle actuel : utiliser un **volume neuf**
pour ce prototype ; un volume existant n'est pas modifié automatiquement.

Après le démarrage de PostgreSQL via Compose, appliquer les migrations (`main`, puis
éventuellement `users`) avec `./src/migration/run-migrations.sh --apply`. Lancer
ensuite l'importeur éphémère depuis la racine du projet :

```bash
HISTORY_START=2026-09-27T00:00:00Z HISTORY_END=2026-09-28T00:00:00Z \
  ./src/seed/run-seed.sh
```

Sans ces variables, la période commence à la date `history_start` de
[`src/seed/infra.conf`](../seed/infra.conf) et s'arrête à l'instant du lancement.
Le script construit l'image, attache le conteneur au réseau `demo_project_default`,
monte le TOML en lecture seule et charge les identifiants depuis
`src/database/.env.postgres`. Le réseau peut être remplacé avec `SEED_NETWORK`.
Le conteneur s'arrête une fois l'import terminé. Les événements parents restent
uniques par identifiant externe, mais chaque réception ajoute un nouveau détail :
relancer la même période ajoute donc de nouveau ses détails, même si leurs données
sont identiques. Une journée avec 10 000 résultats ou plus
interrompt l'import pour éviter une période tronquée. Les contours sont téléchargés
depuis Natural Earth (domaine public, jeux `ne_110m_admin_0_countries`,
`ne_110m_ocean`, `ne_110m_geography_marine_polys`). Ils sont approximatifs à cette
échelle : les épicentres côtiers et la désignation des océans doivent être interprétés
en conséquence. Hors polygone terrestre, aucun pays n'est attribué ; les régions
marines peuvent recouvrir la zone océanique générique.

`longitude` et `latitude` sont conservées dans `emsc_details`; la colonne `position`
est un point PostGIS 4326 calculé automatiquement (longitude, latitude). Les polygones
des pays, continents et océans et les points disposent d'index GiST. Les codes des
zones utilisent `C:` pour les pays (code Natural Earth A3), `T:` pour les continents
et `O:` pour les océans.

Recherche des zones d'un événement, puis des événements d'un pays :

```sql
SELECT z.kind, z.code, z.name
FROM app_schema.emsc_details AS d
JOIN app_schema.geographic_zone AS z ON ST_Covers(z.boundary, d.position)
WHERE d.emsc_id = :emsc_id;

SELECT e.ext_id, d.magnitude, d.longitude, d.latitude
FROM app_schema.geographic_zone AS z
JOIN app_schema.emsc_details AS d ON ST_Covers(z.boundary, d.position)
JOIN app_schema.emsc AS e ON e.id = d.emsc_id
WHERE z.code = 'C:FRA';
```

Le même filtre fonctionne avec un code `T:` ou `O:`. Pour une distance en mètres,
convertir le point en `geography` dans la requête (`position::geography`).
