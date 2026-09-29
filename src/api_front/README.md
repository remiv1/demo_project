# Frontend utilisateur

Le blueprint `user` gère les pages de création de compte, connexion, enrôlement TOTP et vérification. Flask ne se connecte pas à PostgreSQL et ne lit pas les jetons : il transmet le cookie opaque et les formulaires aux routes `/api/v1/user/*` du backend. Le WebSocket `/ws/events` est ouvert uniquement si le backend confirme une session validée par TOTP.

## Configuration

Configurer les secrets **hors du dépôt** :

- `AUTH_INTERNAL_KEY` : valeur aléatoire identique sur `api-back` et `api-front`, pour les appels internes d'authentification ;
- `OTP_ENCRYPTION_KEY` : clé Fernet persistante, uniquement sur `api-back` ; sa perte empêche de vérifier les secrets TOTP existants ;
- `FLASK_SECRET_KEY` : signature du cookie CSRF de Flask ;
- `AUTH_COOKIE_SECURE` : `true` par défaut, nécessite HTTPS. Utiliser `false` uniquement pour des essais locaux en HTTP.

Générer une clé Fernet : `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`.

Les changements des modèles `UserOTP` et `UserSession` nécessitent une migration **à générer et appliquer** avec `src/migration/run-migrations.sh` pour la base `users`. Aucune migration n'est générée ici. Tant qu'elle n'est pas appliquée, le parcours d'authentification n'est pas utilisable.

## Assets

Les styles sont édités dans `static/scss/main.scss`, jamais dans le CSS généré. Depuis `src/api_front`, exécuter `npm ci && npm run build` pour compiler Sass et copier htmx dans `static/js`. Le Dockerfile reconstruit les assets depuis le SCSS et le lockfile.

## Carte historique

La page authentifiée `/map` appartient au blueprint `map`. Elle utilise Leaflet 1.9.4, Supercluster 8.0.1 et Overlapping Marker Spiderfier 0.2.7 depuis jsDelivr, avec versions figées et empreintes SRI. Le fond par défaut est OpenStreetMap standard ; son attribution reste visible. Respecter la politique d'usage de <https://operations.osmfoundation.org/policies/tiles/> (pas de téléchargement massif ni de préchargement hors ligne).

`MAP_TILE_URL` et `MAP_TILE_ATTRIBUTION` permettent de configurer un autre fournisseur. Les requêtes de bibliothèques et de tuiles partent du navigateur vers ces services externes. Une CSP éventuelle doit autoriser jsDelivr pour les scripts/styles et le domaine du fournisseur pour les images ; les styles de positionnement de Leaflet doivent aussi fonctionner.

Le bouton « Appliquer la période » est le seul déclencheur de chargement. Flask relaie `GET /map/events?start=YYYY-MM-DD&end=YYYY-MM-DD` vers `/api/v1/events` avec la clé interne et le cookie opaque ; le backend exige une session validée par TOTP. Les données privées ne sont pas mises en cache. Le frontend utilise un délai d'attente de 60 secondes et conserve la dernière carte chargée en cas d'erreur.

Les dates sont des journées UTC, début et fin inclus. La fin ne peut pas dépasser le même jour du mois suivant, ramené au dernier jour disponible (31 janvier vers 28/29 février). La période initiale remonte d'un mois depuis aujourd'hui. Si le mois précédent n'a pas le même jour, elle commence le 1er du mois courant pour rester valide (31 mars : 1er mars). La validation s'effectue dans le navigateur et dans le backend, sans troncature du résultat. La limite de durée n'est pas une limite de volume : une période très dense peut être coûteuse.

Chaque Feature GeoJSON représente un séisme à sa dernière version connue, sélectionné par date de survenue. Zoom, déplacement, case « Séismes » et magnitude brute min/max sont locaux ; aucune conversion entre échelles n'est effectuée. Les filtres reconstruisent l'index Supercluster ; les points encore superposés au zoom maximal se déploient en éventail au clic. Les popups présentent les coordonnées réelles, et non les positions visuellement décalées. La gravité des autres événements et la vue « Aujourd'hui » en WebSocket restent hors périmètre.
