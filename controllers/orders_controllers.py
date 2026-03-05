import os
from flask import Blueprint, current_app, jsonify, request, url_for

from services.orders_service import (
    build_order_response,
    create_order_from_payload,
    get_order_by_id,
    pay_order_with_credit_card,
    update_order_customer_information,
)


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


@orders_bp.put("/order/<int:order_id>")
def update_order(order_id: int):
    """
    Met à jour les informations d'une commande.
    - Si le payload contient "credit_card", appelle le service de paiement distant.
    - Si le payload contient "order" (email + shipping_information), met à jour les infos client.
    Si le payload est invalide, retourne une réponse d'erreur avec un code 422.
    Si la commande n'existe pas, retourne une réponse d'erreur avec un code 404.
    """
    payload = request.get_json(silent=True) or {}

    if "credit_card" in payload:
        payment_url = current_app.config.get("PAYMENT_URL") or os.environ.get("PAYMENT_URL", "")
        order, error_body, error_status = pay_order_with_credit_card(order_id, payload, payment_url)
    else:
        order, error_body, error_status = update_order_customer_information(order_id, payload)

    if error_body:
        return jsonify(error_body), error_status

    return jsonify(build_order_response(order))
    