import models
import pytest


def test_create_order_success_returns_302_and_location(client):
    response = client.post(
        "/order",
        json={"product": {"id": 1, "quantity": 2}},
    )

    assert response.status_code == 302
    assert response.headers["Location"].startswith("/order/")


def test_create_order_missing_fields_returns_422(client):
    response = client.post("/order", json={})

    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "product": {
                "code": "missing-fields",
                "name": "La création d'une commande nécessite un produit",
            }
        }
    }


def test_create_order_out_of_inventory_returns_422(client):
    models.Product.create(
        id=99,
        name="Out product",
        type="test",
        description="Not available",
        image="x.jpg",
        height=1,
        weight=1,
        price=1.0,
        in_stock=False,
    )

    response = client.post(
        "/order",
        json={"product": {"id": 99, "quantity": 1}},
    )

    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "product": {
                "code": "out-of-inventory",
                "name": "Le produit demandé n'est pas en inventaire",
            }
        }
    }
