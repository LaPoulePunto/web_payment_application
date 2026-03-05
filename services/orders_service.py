import json
import urllib.request
import urllib.error
import models

TAX_RATES_BY_PROVINCE = {
    "QC": 0.15,
    "ON": 0.13,
    "AB": 0.05,
    "BC": 0.12,
    "NS": 0.14,
}


def create_order_from_payload(payload: dict):
    """
    Crée une commande à partir du payload de la requête.
    Le payload doit contenir un champ "product" avec un objet contenant les champs "id" et "quantity".
    Si le payload est invalide ou si le produit n'est pas en stock, retourne une réponse d'erreur avec un code 422.
    Si la commande est créée avec succès, retourne l'objet Order créé.
    """
    product_payload = (payload or {}).get("product")

    if (
        not isinstance(product_payload, dict)
        or "id" not in product_payload
        or "quantity" not in product_payload
        or not isinstance(product_payload["quantity"], int)
        or product_payload["quantity"] < 1
    ):
        return None, {
            "errors": {
                "product": {
                    "code": "missing-fields",
                    "name": "La création d'une commande nécessite un produit",
                }
            }
        }, 422

    product_id = product_payload["id"]
    quantity = product_payload["quantity"]

    product = models.Product.get_or_none(models.Product.id == product_id)
    if product is None or not product.in_stock:
        return None, {
            "errors": {
                "product": {
                    "code": "out-of-inventory",
                    "name": "Le produit demandé n'est pas en inventaire",
                }
            }
        }, 422

    order = models.Order.create(
        product=product,
        quantity=quantity,
    )
    return order, None, None


def get_order_by_id(order_id: int):
    """
    Retourne les détails d'une commande à partir de son ID.
    Si la commande n'existe pas, retourne None.
    """
    return models.Order.get_or_none(models.Order.id == order_id)


def _compute_shipping_price(total_weight_grams: int) -> int:
    """
    Retourne le prix d'expédition en fonction du poids total de la commande.
     - 5$ pour les commandes de 500g ou moins
     - 10$ pour les commandes entre 500g et 2kg
     - 25$ pour les commandes de plus de 2kg
    """
    if total_weight_grams <= 500:
        return 5
    if total_weight_grams < 2000:
        return 10
    return 25


def _serialize_shipping_information(order: models.Order) -> dict:
    """
    Retourne les informations d'expédition d'une commande sous forme de dictionnaire.
    Si la commande n'a pas d'informations d'expédition, retourne un dictionnaire vide.
    """
    shipping = models.ShippingInformation.get_or_none(models.ShippingInformation.order == order)
    if shipping is None:
        return {}

    return {
        "country": shipping.country,
        "address": shipping.address,
        "postal_code": shipping.postal_code,
        "city": shipping.city,
        "province": shipping.province,
    }


def _serialize_credit_card(order: models.Order) -> dict:
    """
    Retourne les informations de la carte de crédit d'une commande sous forme de dictionnaire.
    Si la commande n'a pas de carte de crédit, retourne un dictionnaire vide.
    """
    card = models.CreditCard.get_or_none(models.CreditCard.order == order)
    if card is None:
        return {}

    return {
        "name": card.name,
        "first_digits": card.first_digits,
        "last_digits": card.last_digits,
        "expiration_year": card.expiration_year,
        "expiration_month": card.expiration_month,
    }


def _serialize_transaction(order: models.Order) -> dict:
    """
    Retourne les informations de la transaction d'une commande sous forme de dictionnaire.
    Si la commande n'a pas de transaction, retourne un dictionnaire vide.
    """
    transaction = models.Transaction.get_or_none(models.Transaction.order == order)
    if transaction is None:
        return {}

    return {
        "id": transaction.transaction_id,
        "success": transaction.success,
        "amount_charged": transaction.amount_charged,
    }


def build_order_response(order: models.Order) -> dict:
    """
    Retourne les détails d'une commande sous forme de dictionnaire, en appliquant les taxes et en calculant le prix d'expédition.
    """
    shipping_information = _serialize_shipping_information(order)
    province = shipping_information.get("province", "").upper()
    tax_rate = TAX_RATES_BY_PROVINCE.get(province, 0.0)

    total_price = order.product.price * order.quantity
    total_price_tax = round(total_price * (1 + tax_rate), 2)
    total_weight_grams = order.product.weight * order.quantity
    shipping_price = _compute_shipping_price(total_weight_grams)

    return {
        "order": {
            "id": order.id,
            "total_price": total_price,
            "total_price_tax": total_price_tax,
            "email": order.email,
            "credit_card": _serialize_credit_card(order),
            "shipping_information": shipping_information,
            "paid": order.paid,
            "transaction": _serialize_transaction(order),
            "product": {
                "id": order.product.id,
                "quantity": order.quantity,
            },
            "shipping_price": shipping_price,
        }
    }


def update_order_customer_information(order_id: int, payload: dict):
    """
    Met à jour les informations d'une commande à partir du payload de la requête.
    Le payload doit contenir les champs "customer_name" et "customer_email".
    Si le payload est invalide, retourne une réponse d'erreur avec un code 422
    Si la commande n'existe pas, retourne une réponse d'erreur avec un code 404.
    Si la mise à jour est réussie, retourne les détails de la commande mise à jour
    """
    order = get_order_by_id(order_id)
    if order is None:
        return None, {"error": "Order not found"}, 404

    order_payload = (payload or {}).get("order")
    shipping_payload = (order_payload or {}).get("shipping_information") if isinstance(order_payload, dict) else None

    required_shipping_fields = ["country", "address", "postal_code", "city", "province"]
    has_missing_fields = (
        not isinstance(order_payload, dict)
        or "email" not in order_payload
        or not isinstance(order_payload.get("email"), str)
        or not order_payload.get("email")
        or not isinstance(shipping_payload, dict)
        or any(field not in shipping_payload or not shipping_payload.get(field) for field in required_shipping_fields)
    )

    if has_missing_fields:
        return None, {
            "errors": {
                "order": {
                    "code": "missing-fields",
                    "name": "Il manque un ou plusieurs champs qui sont obligatoires",
                }
            }
        }, 422

    order.email = order_payload["email"]
    order.save()

    models.ShippingInformation.insert(
        order=order,
        country=shipping_payload["country"],
        address=shipping_payload["address"],
        postal_code=shipping_payload["postal_code"],
        city=shipping_payload["city"],
        province=shipping_payload["province"],
    ).on_conflict(
        conflict_target=[models.ShippingInformation.order],
        preserve=[
            models.ShippingInformation.country,
            models.ShippingInformation.address,
            models.ShippingInformation.postal_code,
            models.ShippingInformation.city,
            models.ShippingInformation.province,
        ],
    ).execute()

    order = get_order_by_id(order_id)
    return order, None, None


def pay_order_with_credit_card(order_id: int, payload: dict, payment_url: str):
    """
    Applique une carte de crédit à une commande et appelle le service de paiement distant.
    Le payload doit contenir un champ "credit_card".
    Retourne (order, error_body, error_status).
    """
    order = get_order_by_id(order_id)
    if order is None:
        return None, {"error": "Order not found"}, 404

    credit_card_payload = (payload or {}).get("credit_card")

    # On ne peut pas envoyer credit_card ET shipping_information/email ensemble
    order_payload = (payload or {}).get("order")
    if order_payload is not None:
        return None, {
            "errors": {
                "order": {
                    "code": "missing-fields",
                    "name": "Les informations du client sont nécessaire avant d'appliquer une carte de crédit",
                }
            }
        }, 422

    if not isinstance(credit_card_payload, dict):
        return None, {
            "errors": {
                "order": {
                    "code": "missing-fields",
                    "name": "Les informations du client sont nécessaire avant d'appliquer une carte de crédit",
                }
            }
        }, 422

    # Vérifier que la commande a déjà été payée
    if order.paid:
        return None, {
            "errors": {
                "order": {
                    "code": "already-paid",
                    "name": "La commande a déjà été payée.",
                }
            }
        }, 422

    # Vérifier que l'email et les infos d'expédition sont présents
    shipping = models.ShippingInformation.get_or_none(models.ShippingInformation.order == order)
    if not order.email or shipping is None:
        return None, {
            "errors": {
                "order": {
                    "code": "missing-fields",
                    "name": "Les informations du client sont nécessaire avant d'appliquer une carte de crédit",
                }
            }
        }, 422

    # Calculer le montant total (total_price_tax + shipping_price) en cents
    province = shipping.province.upper()
    tax_rate = TAX_RATES_BY_PROVINCE.get(province, 0.0)
    total_price = order.product.price * order.quantity
    total_price_tax = round(total_price * (1 + tax_rate), 2)
    total_weight_grams = order.product.weight * order.quantity
    shipping_price = _compute_shipping_price(total_weight_grams)
    amount_charged = round((total_price_tax + shipping_price) * 100)

    # Forcer HTTPS pour éviter les redirections HTTP→HTTPS
    if payment_url.startswith("http://"):
        payment_url = "https://" + payment_url[len("http://"):]

    # Appel au service de paiement distant
    request_body = json.dumps({
        "credit_card": credit_card_payload,
        "amount_charged": amount_charged,
    }).encode("utf-8")

    req = urllib.request.Request(
        payment_url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            response_data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        errors = json.loads(raw).get("errors", {}) if raw.strip() else {}
        # Retourner l'erreur du service distant telle quelle
        return None, {"credit_card": errors.get("credit_card", {"code": "card-declined", "name": "La carte de crédit a été déclinée."})}, 422

    # Persister les infos de carte de crédit retournées
    cc_data = response_data.get("credit_card", {})
    models.CreditCard.insert(
        order=order,
        name=cc_data.get("name"),
        first_digits=cc_data.get("first_digits"),
        last_digits=cc_data.get("last_digits"),
        expiration_year=cc_data.get("expiration_year"),
        expiration_month=cc_data.get("expiration_month"),
    ).on_conflict(
        conflict_target=[models.CreditCard.order],
        preserve=[
            models.CreditCard.name,
            models.CreditCard.first_digits,
            models.CreditCard.last_digits,
            models.CreditCard.expiration_year,
            models.CreditCard.expiration_month,
        ],
    ).execute()

    # Persister la transaction
    tx_data = response_data.get("transaction", {})
    models.Transaction.insert(
        order=order,
        transaction_id=tx_data.get("id"),
        success=tx_data.get("success"),
        amount_charged=tx_data.get("amount_charged"),
    ).on_conflict(
        conflict_target=[models.Transaction.order],
        preserve=[
            models.Transaction.transaction_id,
            models.Transaction.success,
            models.Transaction.amount_charged,
        ],
    ).execute()

    # Marquer la commande comme payée
    order.paid = True
    order.save()

    order = get_order_by_id(order_id)
    return order, None, None
