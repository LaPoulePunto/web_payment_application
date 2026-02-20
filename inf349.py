from flask import Flask

from models import db, initialize_db

app = Flask(__name__)


@app.cli.command("init-db")
def init_db_command():
    initialize_db()
