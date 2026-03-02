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


def test_get_order_returns_created_order(client):
    create_response = client.post(
        "/order",
        json={"product": {"id": 1, "quantity": 3}},
    )
    location = create_response.headers["Location"]

    get_response = client.get(location)
    payload = get_response.get_json()

    assert get_response.status_code == 200
    assert payload["order"]["id"] is not None
    assert payload["order"]["total_price"] == pytest.approx(84.3)
    assert payload["order"]["total_price_tax"] == 84.3
    assert payload["order"]["email"] is None
    assert payload["order"]["credit_card"] == {}
    assert payload["order"]["shipping_information"] == {}
    assert payload["order"]["transaction"] == {}
    assert payload["order"]["paid"] is False
    assert payload["order"]["shipping_price"] == 10
    assert payload["order"]["product"]["id"] == 1
    assert payload["order"]["product"]["quantity"] == 3


def test_get_order_applies_tax_from_shipping_province(client):
    create_response = client.post(
        "/order",
        json={"product": {"id": 1, "quantity": 1}},
    )
    location = create_response.headers["Location"]
    order_id = int(location.split("/")[-1])
    order = models.Order.get_by_id(order_id)

    models.ShippingInformation.create(
        order=order,
        country="Canada",
        address="1 rue test",
        postal_code="G1G1G1",
        city="Quebec",
        province="QC",
    )

    get_response = client.get(location)
    payload = get_response.get_json()

    assert get_response.status_code == 200
    assert payload["order"]["total_price"] == pytest.approx(28.1)
    assert payload["order"]["total_price_tax"] == 32.31
    assert payload["order"]["shipping_information"]["province"] == "QC"
    assert payload["order"]["shipping_price"] == 5


def test_put_order_updates_email_and_shipping_information(client):
    create_response = client.post(
        "/order",
        json={"product": {"id": 1, "quantity": 1}},
    )
    location = create_response.headers["Location"]

    response = client.put(
        location,
        json={
            "order": {
                "email": "jgnault@uqac.ca",
                "shipping_information": {
                    "country": "Canada",
                    "address": "201, rue Président-Kennedy",
                    "postal_code": "G7X 3Y7",
                    "city": "Chicoutimi",
                    "province": "QC",
                },
            }
        },
    )

    payload = response.get_json()

    assert response.status_code == 200
    assert payload["order"]["email"] == "jgnault@uqac.ca"
    assert payload["order"]["shipping_information"]["country"] == "Canada"
    assert payload["order"]["shipping_information"]["address"] == "201, rue Président-Kennedy"
    assert payload["order"]["shipping_information"]["postal_code"] == "G7X 3Y7"
    assert payload["order"]["shipping_information"]["city"] == "Chicoutimi"
    assert payload["order"]["shipping_information"]["province"] == "QC"
    assert payload["order"]["product"]["id"] == 1
    assert payload["order"]["product"]["quantity"] == 1
    assert payload["order"]["paid"] is False
    assert payload["order"]["total_price"] == pytest.approx(28.1)
    assert payload["order"]["total_price_tax"] == 32.31
    assert payload["order"]["shipping_price"] == 5
    assert payload["order"]["credit_card"] == {}
    assert payload["order"]["transaction"] == {}


def test_put_order_returns_404_for_missing_order(client):
    response = client.put(
        "/order/999999",
        json={
            "order": {
                "email": "jgnault@uqac.ca",
                "shipping_information": {
                    "country": "Canada",
                    "address": "201, rue Président-Kennedy",
                    "postal_code": "G7X 3Y7",
                    "city": "Chicoutimi",
                    "province": "QC",
                },
            }
        },
    )

    assert response.status_code == 404


def test_put_order_missing_fields_returns_422(client):
    create_response = client.post(
        "/order",
        json={"product": {"id": 1, "quantity": 1}},
    )
    location = create_response.headers["Location"]

    response = client.put(
        location,
        json={
            "order": {
                "shipping_information": {
                    "country": "Canada",
                    "province": "QC",
                }
            }
        },
    )

    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "missing-fields",
                "name": "Il manque un ou plusieurs champs qui sont obligatoires",
            }
        }
    }
