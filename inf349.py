import os
import models
from flask import Flask, jsonify
from controllers.orders_controllers import orders_bp
from services.products_importer import import_products_from_url

from models import initialize_db

def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        TESTING=False,
        DATABASE_PATH="inf349.db",
    )

    if test_config:
        app.config.update(test_config)

    @app.cli.command("init-db")
    def init_db_command():
        initialize_db(app.config["DATABASE_PATH"])

    initialize_db(app.config["DATABASE_PATH"])

    if not app.config["TESTING"]:
        api_url = os.environ.get("PRODUCTS_URL")
        if api_url:
            import_products_from_url(api_url)

    @app.get('/')
    def products_get():
        products = list(models.Product.select().dicts())
        return jsonify({"products": products})

    app.register_blueprint(orders_bp)

    return app
