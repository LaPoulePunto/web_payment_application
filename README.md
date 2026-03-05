# INF349 — Application de paiement de commandes

**Équipe :** Oscar Neveux, Thibault Martin, Martin Vidal

Application Web Flask de gestion de commandes Internet avec API REST.

## Stack

Pour ce projet, nous utilisons Flask, Peewee, uv pour les dépendances et Docker.

## Avant de lancer le projet

**1. Installer uv** (gestionnaire de dépendances python) : [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

**2. Installer les dépendances :**
```bash
uv sync
```

**3. Configurer le fichier `.env` :**
```bash
cp .env.example .env
```
Le fichier `.env.example` contient déjà les URLs des services distants, aucune modification n'est nécessaire.

## Lancer le projet

```bash
flask --app inf349:create_app --debug run
```

L'API est disponible sur `http://localhost:5000`.

## Lancer les tests

```bash
uv run pytest
```

## Lancer la couverture de tests

```bash
uv run pytest --cov=. --cov-report=html
```

Le rapport HTML est généré dans `htmlcov/index.html`.

## Suite Postman

Une collection Postman est disponible dans `postman/INF349.postman_collection.json`.

Elle couvre les requêtes suivantes dans l'ordre :

- `GET /`
- `POST /order`
- `GET /order/<id>`
- `PUT /order/<id>`
- `PUT /order/<id>`

### Exécuter la suite

1. Lancer l'application Flask.
2. Importer la collection `postman/INF349.postman_collection.json` dans Postman.
3. Vérifier la variable `baseUrl` (par défaut `http://localhost:5000`).
4. Remplir le `orderId`.
5. Exécuter la collection avec **Collection Runner**.


