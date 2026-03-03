def test_get_products(client):
    """
    Teste que l'endpoint GET / retourne la liste des produits.
    """
    response = client.get("/")
    assert response.status_code == 200

    data = response.get_json()
    assert "products" in data
    assert len(data["products"]) == 1
    assert data["products"][0]["id"] == 1
    assert data["products"][0]["name"] == "Brown eggs"