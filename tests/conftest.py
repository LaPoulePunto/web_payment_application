import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import models
from inf349 import create_app

@pytest.fixture
def app(tmp_path):
    test_db_path = tmp_path / "test.db"
    app = create_app({
        "TESTING": True,
        "DATABASE_PATH": str(test_db_path),
    })

    models.Product.create(
        id=1,
        name="Brown eggs",
        type="dairy",
        description="Raw organic brown eggs in a basket",
        image="0.jpg",
        height=600,
        weight=400,
        price=28.1,
        in_stock=True,
    )

    yield app

    if not models.db.is_closed():
        models.db.close()

@pytest.fixture
def client(app):
    return app.test_client()