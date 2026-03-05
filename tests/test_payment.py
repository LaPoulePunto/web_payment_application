import json
from unittest.mock import patch, MagicMock
import pytest


VALID_CARD = {
    "name": "John Doe",
    "number": "4242 4242 4242 4242",
    "expiration_year": 2027,
    "cvv": "123",
    "expiration_month": 9,
}

DECLINED_CARD = {
    "name": "John Doe",
    "number": "4000 0000 0000 0002",
    "expiration_year": 2027,
    "cvv": "123",
    "expiration_month": 9,
}

PAYMENT_RESPONSE = {
    "credit_card": {
        "name": "John Doe",
        "first_digits": "4242",
        "last_digits": "4242",
        "expiration_year": 2027,
        "expiration_month": 9,
    },
    "transaction": {
        "id": "wgEQ4zAUdYqpr21rt8A10dDrKbfcLmqi",
        "success": True,
        "amount_charged": 3831,
    },
}


def _create_order_with_shipping(client):
    """Helper : crée une commande et y ajoute email + shipping."""
    create_resp = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    location = create_resp.headers["Location"]

    client.put(
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
    return location


def _mock_payment_success():
    """Retourne un mock urllib qui simule une réponse 200 du service distant."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(PAYMENT_RESPONSE).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch("services.orders_service.urllib.request.urlopen", return_value=mock_resp)


def test_pay_order_success(client):
    location = _create_order_with_shipping(client)

    with _mock_payment_success():
        response = client.put(location, json={"credit_card": VALID_CARD})

    payload = response.get_json()

    assert response.status_code == 200
    assert payload["order"]["paid"] is True
    assert payload["order"]["credit_card"]["name"] == "John Doe"
    assert payload["order"]["credit_card"]["first_digits"] == "4242"
    assert payload["order"]["credit_card"]["last_digits"] == "4242"
    assert payload["order"]["transaction"]["success"] is True
    assert payload["order"]["transaction"]["id"] == "wgEQ4zAUdYqpr21rt8A10dDrKbfcLmqi"


def test_pay_order_marks_paid_on_get(client):
    location = _create_order_with_shipping(client)

    with _mock_payment_success():
        client.put(location, json={"credit_card": VALID_CARD})

    get_resp = client.get(location)
    assert get_resp.get_json()["order"]["paid"] is True


def test_pay_order_already_paid_returns_422(client):
    location = _create_order_with_shipping(client)

    with _mock_payment_success():
        client.put(location, json={"credit_card": VALID_CARD})

    with _mock_payment_success():
        response = client.put(location, json={"credit_card": VALID_CARD})

    assert response.status_code == 422
    assert response.get_json() == {
        "errors": {
            "order": {
                "code": "already-paid",
                "name": "La commande a déjà été payée.",
            }
        }
    }


def test_pay_order_without_shipping_returns_422(client):
    create_resp = client.post("/order", json={"product": {"id": 1, "quantity": 1}})
    location = create_resp.headers["Location"]

    response = client.put(location, json={"credit_card": VALID_CARD})

    assert response.status_code == 422
    assert response.get_json()["errors"]["order"]["code"] == "missing-fields"


def test_pay_order_card_declined_returns_422(client):
    import urllib.error

    location = _create_order_with_shipping(client)

    declined_body = json.dumps({
        "errors": {
            "credit_card": {
                "code": "card-declined",
                "name": "La carte de crédit a été déclinée",
            }
        }
    }).encode()
    http_error = urllib.error.HTTPError(
        url="", code=422, msg="Unprocessable Entity", hdrs={}, fp=None
    )
    http_error.read = lambda: declined_body

    with patch("services.orders_service.urllib.request.urlopen", side_effect=http_error):
        response = client.put(location, json={"credit_card": DECLINED_CARD})

    assert response.status_code == 422
    assert response.get_json()["credit_card"]["code"] == "card-declined"


def test_pay_order_mixed_payload_returns_422(client):
    """Envoyer credit_card ET order ensemble doit être refusé."""
    location = _create_order_with_shipping(client)

    response = client.put(
        location,
        json={
            "credit_card": VALID_CARD,
            "order": {"email": "x@x.com"},
        },
    )

    assert response.status_code == 422
    assert response.get_json()["errors"]["order"]["code"] == "missing-fields"
