import graphene
from graphene import ObjectType, String, Int
from stocks.schemas.product import Product
from db import get_redis_conn
from db import get_sqlalchemy_session
from stocks.models.product import Product as ProductModel
from stocks.models.stock import Stock

class Query(ObjectType):       
    product = graphene.Field(Product, id=String(required=True))
    stock_level = Int(product_id=String(required=True))
    
    def resolve_product(self, info, id):
        """ Create an instance of Product based on complete info from Redis (quantity + product details) """
    
        # Get ALL product data from Redis (quantity + name + sku + price)
        redis_client = get_redis_conn()
        product_data = redis_client.hgetall(f"stock:{id}")
        
        if not product_data:
            return None
        
        # Si les informations produit ne sont pas dans Redis, fallback vers MySQL
        if not product_data.get('name'):
            session = get_sqlalchemy_session()
            result = session.query(
                ProductModel.name,
                ProductModel.sku,
                ProductModel.price
            ).filter(ProductModel.id == int(id)).first()
            
            if result:
                return Product(
                    id=id,
                    name=result.name,
                    sku=result.sku,
                    price=float(result.price),
                    quantity=int(product_data.get('quantity', 0))
                )
            else:
                return Product(
                    id=id,
                    name=f"Product {id}",
                    sku="N/A",
                    price=0.0,
                    quantity=int(product_data.get('quantity', 0))
                )
        
        # Utiliser toutes les données de Redis (approche optimisée)
        return Product(
            id=id,
            name=product_data.get('name', f"Product {id}"),
            sku=product_data.get('sku', 'N/A'),
            price=float(product_data.get('price', 0.0)),
            quantity=int(product_data.get('quantity', 0))
        )
    
    def resolve_stock_level(self, info, product_id):
        """ Retrieve stock quantity from Redis """
        redis_client = get_redis_conn()
        quantity = redis_client.hget(f"stock:{product_id}", "quantity")
        return int(quantity) if quantity else 0