"""
Tests for orders manager
SPDX - License - Identifier: LGPL - 3.0 - or -later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
import pytest
from store_manager import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    result = client.get('/health-check')
    assert result.status_code == 200
    assert result.get_json() == {'status':'ok'}

def test_stock_flow(client):
    """
    Smoke test pour vérifier le flux complet de gestion des stocks.
    Ce test vérifie que le processus de base fonctionne de manière consistante :
    produit -> stock -> commande -> mise à jour du stock
    """
    
    # 0. Vérification de santé de l'API d'abord
    health_response = client.get('/health-check')
    assert health_response.status_code == 200
    print(f"✓ API Health Check: {health_response.get_json()}")
    
    # 1. Créez un article (`POST /products`)
    import time
    timestamp = str(int(time.time()))
    product_payload = f'{{"name": "Some item", "sku": "ABCDEF{timestamp}", "price": 5.55}}'
    response = client.post('/products',
                          data=product_payload,
                          content_type='application/json')
    

    
    assert response.status_code == 201, f"Création produit échouée: {response.status_code}"
    product_response = response.get_json()
    assert product_response['product_id'] > 0
    product_id = product_response['product_id']
    print(f"✓ Produit créé avec ID: {product_id}")

    # 2. Créez un utilisateur pour les commandes (`POST /users`)
    user_payload = f'{{"name": "Jane Doe", "email": "jd{timestamp}@example.ca"}}'
    response = client.post('/users',
                          data=user_payload,
                          content_type='application/json')
    
    assert response.status_code == 201
    user_response = response.get_json()
    assert user_response['user_id'] > 0
    user_id = user_response['user_id']
    print(f"✓ Utilisateur créé avec ID: {user_id}")

    # 3. Ajoutez 5 unités au stock de cet article (`POST /stocks`)
    stock_data = {'product_id': product_id, 'quantity': 5}
    response = client.post('/stocks',
                          data=json.dumps(stock_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    stock_response = response.get_json()
    stock_id = stock_response.get('stock_id') or stock_response.get('id')
    print(f"✓ Stock créé - 5 unités ajoutées")

    # 4. Vérifiez le stock, votre article devra avoir 5 unités dans le stock (`GET /stocks/:id`)
    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 201
    stock_check = response.get_json()
    initial_quantity = stock_check['quantity']
    assert initial_quantity == 5
    print(f"✓ Stock vérifié: {initial_quantity} unités disponibles")

    # 5. Faites une commande de l'article que vous avez créé, 2 unités (`POST /orders`)
    order_data = {
        'user_id': user_id,
        'items': [{'product_id': product_id, 'quantity': 2}]
    }
    response = client.post('/orders',
                          data=json.dumps(order_data),
                          content_type='application/json')
    
    assert response.status_code == 201
    order_response = response.get_json()
    order_id = order_response['order_id']
    print(f"✓ Commande créée avec ID: {order_id} - 2 unités commandées")

    # 6. Vérifiez le stock encore une fois (`GET /stocks/:id`)
    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 201
    stock_after_order = response.get_json()
    remaining_quantity = stock_after_order['quantity']
    assert remaining_quantity == 3  # 5 - 2 = 3
    print(f"✓ Stock après commande: {remaining_quantity} unités restantes")

    # 7. Étape extra: supprimez la commande et vérifiez le stock de nouveau
    # Le stock devrait augmenter après la suppression de la commande
    response = client.delete(f'/orders/{order_id}')
    assert response.status_code in [200, 204]  # Accepter les deux codes de succès
    print(f"✓ Commande {order_id} supprimée")

    # 8. Vérification finale du stock après suppression de la commande
    response = client.get(f'/stocks/{product_id}')
    assert response.status_code == 201
    final_stock = response.get_json()
    final_quantity = final_stock['quantity']
    assert final_quantity == 5  # Le stock devrait être restauré à 5
    print(f"✓ Stock après suppression de commande: {final_quantity} unités (restauré)")

    print("Smoke test du flux de stock terminé avec succès!")