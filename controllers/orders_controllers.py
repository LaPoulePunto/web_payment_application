from flask import Blueprint, jsonify, request, url_for

from services.orders_service import build_order_response, create_order_from_payload, get_order_by_id


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


@orders_bp.get("/order/<int:order_id>")
def get_order(order_id: int):
    """
    Retourne les détails d'une commande à partir de son ID.
    Si la commande n'existe pas, retourne une réponse d'erreur avec un code 404.
    """
    order = get_order_by_id(order_id)
    if order is None:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(build_order_response(order))
