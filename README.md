# INF349 — Application de paiement de commandes

**Équipe :** Oscar Neveux, Thibault Martin, Martin Vidal

Application Web Flask de gestion de commandes Internet avec API REST.

## Stack

Pour ce projet, nous utilisons Flask, Peewee, uv pour les dépendances et Docker.

## Avant de lancer le projet

Il faut créer un fichier .env avec la variable d'environnement de l'url de l'API, afin de récupérer l'ensemble des produits.
Pour cela copier cette ligne dans votre fichier et remplacez la valeur `url_de_l_api` par l'url de votre api:
```bash
PRODUCTS_URL="url_de_l_api"
PAYMENT_URL="url_de_l_api"
```

## Lancer le projet

```bash
flask --app inf349:create_app --debug run
```

L'API est disponible sur `http://localhost:5000`.

## Lancer les tests

```bash
uv run pytest
```