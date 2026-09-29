# API backend

## API cartographique

`GET /api/v1/events?start=YYYY-MM-DD&end=YYYY-MM-DD` retourne une `FeatureCollection`
GeoJSON pour les séismes. La clé interne `X-Frontend-Key` et une session TOTP validée
sont obligatoires. La période, en journées UTC incluses, est limitée à un mois calendaire
glissant (même jour du mois suivant, ajusté au dernier jour disponible).

La date de survenue `emsc.initial_datetime` décide de l'appartenance à la période.
La version retenue est celle dont `emsc_details.event_datetime` est la plus récente,
puis l'identifiant de détail le plus élevé en cas d'égalité. Elle peut avoir été révisée
après la période sélectionnée. Les pays/continents sont résolus avec `ST_Covers`.
La requête ne modifie pas l'ingestion et ne limite pas silencieusement le nombre de points.
Les coordonnées GeoJSON sont ordonnées longitude, latitude ; les heures sont sérialisées en UTC.

## Redis Streams

Le backend relaie les messages JSON du WebSocket EMSC vers Redis. Le worker effectue ensuite l'ingestion ; après commit, il ajoute la notification au Stream `new_event` et acquitte le message brut :

```text
WebSocket EMSC -> ingest:earthquakes:raw -> worker -> PostgreSQL/commit -> new_event -> Flask /ws/events
```

Le message EMSC brut est sérialisé en JSON dans le champ `payload` du Stream d'ingestion. La notification sérialisée dans le champ `payload` de `new_event` contient `type` et `event` ; pour les séismes, le worker enrichit `event.properties` avec `country` et `continent`, résolus avec `ST_Covers` (valeurs `null` si aucune zone ne correspond). Flask ajoute ensuite l'ID Redis avant envoi au navigateur. Les routes Redis de développement utilisent toujours `NewSeismMessage` ; leur format ne définit pas celui du relais EMSC.

### Groupes de consommateurs

Un groupe est créé avec une position de départ explicite :

- `0-0` permet de relire tous les messages déjà présents dans le Stream. C'est le choix par défaut pour éviter une perte silencieuse lors du démarrage d'un nouveau consommateur.
- `$` permet de ne consommer que les messages publiés après la création du groupe. Il convient aux consommateurs qui ne nécessitent pas de rattrapage.

Les consommateurs lisent les messages avec leur nom de consommateur, puis les acquittent après commit et publication de la notification. Le worker reprend au démarrage les messages en attente de son propre consommateur.

### Rôles Redis

Les ACL Redis séparent les responsabilités :

- l'utilisateur worker publie les événements EMSC, consomme les Streams et écrit dans `new_event` ;
- l'utilisateur application lit les notifications du Stream dans Flask ;
- l'utilisateur monitor dispose d'un accès en lecture.

Les routes de gestion des Streams sont des routes internes de développement. Elles ne doivent pas être exposées à des clients non authentifiés en production.

### Fiabilité de la publication

Les repositories `EarthquakesRepo` et `FloodRepo` ne sont pas encore totalement implémentés : aucun commit, acquittement ou `new_event` n'est produit pour ces messages. Chaque WebSocket lit `new_event` avec son propre curseur, sans groupe partagé : tous les utilisateurs connectés reçoivent les mêmes notifications. À la première connexion, Flask se place après la dernière notification ; lors d'une reconnexion dans la même page, le navigateur transmet le dernier ID reçu et Flask reprend après cet ID. Un rechargement complet perd ce curseur. Aucune limite de rétention n'est encore configurée : le Stream grandira tant qu'il n'est pas nettoyé ; une politique de rétention future réduira la fenêtre de reprise.

Après implémentation des repositories, une interruption entre commit, publication et acquittement pourra produire des notifications en double ; l'ingestion devra être idempotente et une outbox sera nécessaire pour garantir la diffusion.

La route `/ws/events` de Flask exige une session contenant `user_id` et `otp_verified = True`, ainsi qu'une origine correspondant à l'hôte appelé. La connexion utilisateur et la vérification OTP restent à implémenter : la route est donc fermée dans l'état actuel.
