# API backend

## Redis Streams

Le flux Redis est un bus d'événements entre l'ingestion et les consommateurs. Un événement n'est publié qu'après la validation de l'écriture du séisme en base de données :

```text
ingestion EMSC -> validation -> écriture PostgreSQL -> commit -> Redis Stream
```

Chaque message utilise le modèle `NewSeismMessage`. Il contient l'identifiant EMSC, l'identifiant en base (`db_id`), la date et les informations utiles au filtrage. Le contenu est sérialisé en JSON dans le champ `payload` du message Redis afin de préserver le format ISO 8601 des dates et les valeurs textuelles de l'importance.

### Groupes de consommateurs

Un groupe est créé avec une position de départ explicite :

- `0-0` permet de relire tous les messages déjà présents dans le Stream. C'est le choix par défaut pour éviter une perte silencieuse lors du démarrage d'un nouveau consommateur.
- `$` permet de ne consommer que les messages publiés après la création du groupe. Il convient aux consommateurs qui ne nécessitent pas de rattrapage.

Les consommateurs lisent les messages avec leur nom de consommateur, puis les acquittent une fois le traitement terminé. Un message non acquitté reste en attente dans le groupe et peut être repris ultérieurement.

### Rôles Redis

Les ACL Redis séparent les responsabilités :

- l'utilisateur worker crée les groupes et publie les messages Stream ;
- l'utilisateur application consomme, inspecte les messages en attente et les acquitte ;
- l'utilisateur monitor dispose d'un accès en lecture.

Les routes de gestion des Streams sont des routes internes de développement. Elles ne doivent pas être exposées à des clients non authentifiés en production.

### Fiabilité de la publication

La première implémentation publiera l'événement après le commit PostgreSQL. Une interruption entre ces deux opérations peut donc laisser un séisme enregistré sans événement Redis associé. Une table d'outbox transactionnelle, relayée vers Redis par un processus dédié, sera ajoutée lorsque le pipeline d'ingestion en base sera en place.
