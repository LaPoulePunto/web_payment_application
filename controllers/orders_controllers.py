from flask import Blueprint, jsonify, request, url_for

from services.orders_service import create_order_from_payload


orders_bp = Blueprint("orders", __name__)


@orders_bp.post("/order")
def create_order():
    """
    Crée une commande à partir du payload de la requête.
    Le payload doit contenir un champ "product" avec un objet contenant les champs "id" et "quantity".
    Si le payload est invalide ou si le produit n'est pas en stock, retourne une réponse d'erreur avec un code 422.
    Si la commande est créée avec succès, retourne une redirection vers l'endpoint GET /order/<order_id>.
    """
    payload = request.get_json(silent=True) or {}
    order, error_body, error_status = create_order_from_payload(payload)

    if error_body:
        return jsonify(error_body), error_status

    location = url_for("orders.get_order", order_id=order.id)
    return "", 302, {"Location": location}
