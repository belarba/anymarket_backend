from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict
import uvicorn

from . import models, schemas
from .database import SessionLocal, engine, get_db
from .anymarket_client import AnymarketClient

# Criar tabelas no banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Anymarket Backend", version="1.0.0")

# Instanciar cliente da API
anymarket_client = AnymarketClient()

def save_products_to_db(products_data: List[Dict], db: Session):
    """Salva produtos no banco de dados"""
    for product_data in products_data:
        try:
            # Extrair valores seguros, lidando com objetos complexos
            anymarket_id = str(product_data.get("id", ""))
            title = product_data.get("title", "")
            description = product_data.get("description", "")
            price = float(product_data.get("price", 0))
            
            # Brand pode ser um dict ou string
            brand_data = product_data.get("brand", "")
            if isinstance(brand_data, dict):
                brand = brand_data.get("name", "")
            else:
                brand = str(brand_data) if brand_data else ""
            
            # Category pode ser um dict ou string
            category_data = product_data.get("category", "")
            if isinstance(category_data, dict):
                category = category_data.get("name", "")
            else:
                category = str(category_data) if category_data else ""
            
            model = product_data.get("model", "")
            sku = product_data.get("sku", "")
            stock_quantity = int(product_data.get("stockQuantity", 0))
            
            # Verifica se produto já existe
            existing_product = db.query(models.Product).filter(
                models.Product.anymarket_id == anymarket_id
            ).first()
            
            if existing_product:
                # Atualiza produto existente
                existing_product.title = title
                existing_product.description = description
                existing_product.price = price
                existing_product.brand = brand
                existing_product.model = model
                existing_product.category = category
                existing_product.sku = sku
                existing_product.stock_quantity = stock_quantity
                existing_product.updated_at = datetime.now()
            else:
                # Cria novo produto
                new_product = models.Product(
                    anymarket_id=anymarket_id,
                    title=title,
                    description=description,
                    price=price,
                    brand=brand,
                    model=model,
                    category=category,
                    sku=sku,
                    stock_quantity=stock_quantity
                )
                db.add(new_product)
        
        except (ValueError, TypeError) as e:
            print(f"Erro ao processar produto {product_data.get('id')}: {e}")
            continue
    
    db.commit()

def save_orders_to_db(orders_data: List[Dict], db: Session):
    """Salva pedidos no banco de dados"""
    for order_data in orders_data:
        # Verifica se pedido já existe
        existing_order = db.query(models.Order).filter(
            models.Order.anymarket_id == str(order_data.get("id"))
        ).first()
        
        if not existing_order:
            # Cria novo pedido
            order_date = datetime.fromisoformat(
                order_data.get("createdAt", "").replace("Z", "+00:00")
            ) if order_data.get("createdAt") else datetime.now()
            
            new_order = models.Order(
                anymarket_id=str(order_data.get("id")),
                marketplace=order_data.get("marketplace", ""),
                status=order_data.get("status", ""),
                total_amount=float(order_data.get("totalAmount", 0)),
                customer_name=order_data.get("buyer", {}).get("name", ""),
                customer_email=order_data.get("buyer", {}).get("email", ""),
                order_date=order_date
            )
            db.add(new_order)
    
    db.commit()

@app.get("/")
def read_root():
    return {"message": "Anymarket Backend API"}

@app.post("/sync/products")
def sync_products(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos da API Anymarket"""
    def sync_task():
        offset = 0
        limit = 50
        
        while True:
            products_response = anymarket_client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                break
            
            save_products_to_db(products, db)
            offset += limit
            
            # Se retornou menos que o limite, não há mais produtos
            if len(products) < limit:
                break
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização de produtos iniciada"}

@app.post("/sync/orders")
def sync_orders(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza pedidos da API Anymarket"""
    def sync_task():
        offset = 0
        limit = 50
        
        while True:
            orders_response = anymarket_client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                break
            
            save_orders_to_db(orders, db)
            offset += limit
            
            # Se retornou menos que o limite, não há mais pedidos
            if len(orders) < limit:
                break
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização de pedidos iniciada"}

@app.get("/products", response_model=List[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista produtos do banco de dados"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/orders", response_model=List[schemas.Order])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista pedidos do banco de dados"""
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)