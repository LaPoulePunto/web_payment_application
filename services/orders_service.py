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
