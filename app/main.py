from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict
import uvicorn
import logging

from . import models, schemas
from .database import SessionLocal, engine, get_db, test_connection
from .anymarket_client import AnymarketClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Testar conexão com banco
logger.info("Testando conexão com banco de dados...")
if not test_connection():
    logger.error("Falha na conexão com banco de dados!")
    exit(1)

# Criar tabelas no banco
logger.info("Criando tabelas no banco de dados...")
try:
    models.Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelas criadas/verificadas com sucesso")
except Exception as e:
    logger.error(f"❌ Erro ao criar tabelas: {e}")
    exit(1)

app = FastAPI(
    title="Anymarket Backend", 
    version="1.0.0",
    description="API para sincronização de dados da Anymarket com banco PostgreSQL"
)

# Instanciar cliente da API
anymarket_client = AnymarketClient()

def save_products_to_db(products_data: List[Dict], db: Session):
    """Salva produtos no banco de dados"""
    saved_count = 0
    updated_count = 0
    
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
                updated_count += 1
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
                saved_count += 1
        
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar produto {product_data.get('id')}: {e}")
            continue
    
    db.commit()
    logger.info(f"Produtos salvos: {saved_count}, atualizados: {updated_count}")

def save_orders_to_db(orders_data: List[Dict], db: Session):
    """Salva pedidos no banco de dados"""
    saved_count = 0
    
    for order_data in orders_data:
        try:
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
                saved_count += 1
        
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar pedido {order_data.get('id')}: {e}")
            continue
    
    db.commit()
    logger.info(f"Pedidos salvos: {saved_count}")

@app.get("/")
def read_root():
    return {
        "message": "Anymarket Backend API",
        "version": "1.0.0",
        "database": "Neon PostgreSQL",
        "status": "online"
    }

@app.get("/health")
def health_check():
    """Endpoint de saúde da aplicação"""
    try:
        # Testa conexão com banco
        if test_connection():
            return {"status": "healthy", "database": "connected"}
        else:
            return {"status": "unhealthy", "database": "disconnected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/sync/products")
def sync_products(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos da API Anymarket"""
    def sync_task():
        logger.info("Iniciando sincronização de produtos...")
        offset = 0
        limit = 50
        total_products = 0
        
        while True:
            logger.info(f"Buscando produtos: offset {offset}, limit {limit}")
            products_response = anymarket_client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                logger.info("Nenhum produto encontrado. Finalizando sincronização.")
                break
            
            # Criar nova sessão para background task
            db_session = SessionLocal()
            try:
                save_products_to_db(products, db_session)
                total_products += len(products)
                logger.info(f"Total de produtos processados: {total_products}")
            finally:
                db_session.close()
            
            offset += limit
            
            # Se retornou menos que o limite, não há mais produtos
            if len(products) < limit:
                break
        
        logger.info(f"Sincronização de produtos concluída. Total: {total_products}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização de produtos iniciada"}

@app.post("/sync/orders")
def sync_orders(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza pedidos da API Anymarket"""
    def sync_task():
        logger.info("Iniciando sincronização de pedidos...")
        offset = 0
        limit = 50
        total_orders = 0
        
        while True:
            logger.info(f"Buscando pedidos: offset {offset}, limit {limit}")
            orders_response = anymarket_client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                logger.info("Nenhum pedido encontrado. Finalizando sincronização.")
                break
            
            # Criar nova sessão para background task
            db_session = SessionLocal()
            try:
                save_orders_to_db(orders, db_session)
                total_orders += len(orders)
                logger.info(f"Total de pedidos processados: {total_orders}")
            finally:
                db_session.close()
            
            offset += limit
            
            # Se retornou menos que o limite, não há mais pedidos
            if len(orders) < limit:
                break
        
        logger.info(f"Sincronização de pedidos concluída. Total: {total_orders}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização de pedidos iniciada"}

@app.get("/products", response_model=List[schemas.Product])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista produtos do banco de dados"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/count")
def get_products_count(db: Session = Depends(get_db)):
    """Retorna o número total de produtos"""
    count = db.query(models.Product).count()
    return {"total_products": count}

@app.get("/orders", response_model=List[schemas.Order])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista pedidos do banco de dados"""
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/count")
def get_orders_count(db: Session = Depends(get_db)):
    """Retorna o número total de pedidos"""
    count = db.query(models.Order).count()
    return {"total_orders": count}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)