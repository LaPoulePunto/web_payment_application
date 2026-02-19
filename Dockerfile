FROM python:3.8-slim

# Installation d'uv 
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copier uniquement les fichiers nécessaires pour les dépendances
COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

# Copie du reste du projet
COPY . .

ENV FLASK_APP=inf349
ENV FLASK_DEBUG=1

EXPOSE 5000

CMD ["uv", "run", "flask", "run", "--host=0.0.0.0"]