import os
import models
from flask import Flask, jsonify
from services.products_importer import import_products_from_url

from models import db, initialize_db

def create_app() -> Flask:
    app = Flask(__name__)

    @app.cli.command("init-db")
    def init_db_command():
        initialize_db()
    
    initialize_db()

    api_url = os.environ.get("PRODUCTS_URL")

    import_products_from_url(api_url)

    @app.get('/')
    def products_get():
        products = list(models.Product.select().dicts())
        return jsonify({"products": products})


    return app

app = create_app()