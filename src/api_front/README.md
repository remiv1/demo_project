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
