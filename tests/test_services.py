def test_import_products_from_url_function(client):
    """
    Teste que la fonction import_products_from_url insère les produits en base.
    """
    from services.products_importer import import_products_from_url
    from unittest.mock import patch, MagicMock
    import models

    mock_response = MagicMock()
    mock_response.read.return_value = b'{"products": [{"id": 2, "name": "Test Product", "type": "test", "description": "A test product", "image": "test.jpg", "height": 100, "weight": 200, "price": 9.99, "in_stock": true}]}'
    
    with patch("urllib.request.urlopen", return_value=mock_response):
        import_products_from_url("http://fakeapi.com/products")

    response = client.get("/")
    data = response.get_json()
    assert len(data["products"]) == 2
    assert data["products"][1]["id"] == 2
    assert data["products"][1]["name"] == "Test Product"

    assert models.Product.select().where(models.Product.id == 2).exists()