import models

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
