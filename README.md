# INF349 — Application de paiement de commandes

**Équipe :** Oscar Neveux, Thibault Martin, Martin Vidal

Application Web Flask de gestion de commandes Internet avec API REST.

## Stack

Pour ce projet, nous utilisons Flask, Peewee, uv pour les dépendances et Docker.

## Lancer le projet

```bash
docker compose run --rm web uv run flask init-db
docker compose up
```

L'API est disponible sur `http://localhost:5000`.

