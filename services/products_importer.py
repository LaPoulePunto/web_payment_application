import urllib
import json
import models

def import_products_from_url(api_url: str) -> None:
    """
    Récupère des produits depuis une API HTTP et les insère en base.

    Args:
        api_url: URL de l'API source
    
    Return:
        None
    """
    response = urllib.request.urlopen(
        api_url
    )
    data = (json.loads(response.read().decode()))
    products = data.get("products", [])
    models.Product.insert_many(products).on_conflict_ignore().execute()