from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn
import logging

from . import models, schemas
from .database import SessionLocal, engine, get_db
from .anymarket_client import AnymarketClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar tabelas no banco
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Anymarket Backend", version="2.0.0")

# Instanciar cliente da API
anymarket_client = AnymarketClient()

def safe_get_value(data: dict, key: str, default=None):
    """Função auxiliar para extrair valores de forma segura"""
    value = data.get(key, default)
    return value if value is not None else default

def parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    """Converte string de data ISO para datetime"""
    if not date_string:
        return None
    try:
        # Remove 'Z' e adiciona timezone se necessário
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        return None

def extract_address_data(address_data: dict, prefix: str) -> dict:
    """Extrai dados de endereço de forma padronizada"""
    if not address_data:
        return {}
    
    return {
        f"{prefix}_street": safe_get_value(address_data, "street", ""),
        f"{prefix}_number": safe_get_value(address_data, "number", ""),
        f"{prefix}_complement": safe_get_value(address_data, "complement", ""),
        f"{prefix}_neighborhood": safe_get_value(address_data, "neighborhood", ""),
        f"{prefix}_city": safe_get_value(address_data, "city", ""),
        f"{prefix}_state": safe_get_value(address_data, "state", ""),
        f"{prefix}_zip_code": safe_get_value(address_data, "zipCode", ""),
        f"{prefix}_country": safe_get_value(address_data, "country", "BR"),
    }

def save_products_to_db_expanded(products_data: List[Dict], db: Session):
    """Salva produtos no banco de dados com TODOS os campos expandidos"""
    for product_data in products_data:
        try:
            anymarket_id = str(safe_get_value(product_data, "id", ""))
            
            # Extrair dados da categoria
            category_data = safe_get_value(product_data, "category", {})
            category_id = str(category_data.get("id", "")) if isinstance(category_data, dict) else ""
            category_name = category_data.get("name", "") if isinstance(category_data, dict) else str(category_data) if category_data else ""
            category_path = category_data.get("path", "") if isinstance(category_data, dict) else ""
            
            # Extrair dados da marca
            brand_data = safe_get_value(product_data, "brand", {})
            brand_id = str(brand_data.get("id", "")) if isinstance(brand_data, dict) else ""
            brand_name = brand_data.get("name", "") if isinstance(brand_data, dict) else str(brand_data) if brand_data else ""
            brand_partner_id = brand_data.get("partnerId", "") if isinstance(brand_data, dict) else ""
            
            # Extrair dados do NBM
            nbm_data = safe_get_value(product_data, "nbm", {})
            nbm_code = nbm_data.get("id", "") if isinstance(nbm_data, dict) else ""
            
            # Extrair dados da origem
            origin_data = safe_get_value(product_data, "origin", {})
            origin_id = str(origin_data.get("id", "")) if isinstance(origin_data, dict) else ""
            origin_name = origin_data.get("name", "") if isinstance(origin_data, dict) else ""
            
            # Preparar dados do produto
            product_fields = {
                "anymarket_id": anymarket_id,
                "title": safe_get_value(product_data, "title", ""),
                "description": safe_get_value(product_data, "description", ""),
                "model": safe_get_value(product_data, "model", ""),
                "sku": safe_get_value(product_data, "sku", ""),
                "partner_id": safe_get_value(product_data, "partnerId", ""),
                
                # Categoria e marca
                "category_id": category_id,
                "category_name": category_name,
                "category_path": category_path,
                "brand_id": brand_id,
                "brand_name": brand_name,
                "brand_partner_id": brand_partner_id,
                
                # Preços
                "price": float(safe_get_value(product_data, "price", 0)),
                "cost_price": float(safe_get_value(product_data, "costPrice", 0)) if product_data.get("costPrice") else None,
                "promotional_price": float(safe_get_value(product_data, "promotionalPrice", 0)) if product_data.get("promotionalPrice") else None,
                "price_factor": float(safe_get_value(product_data, "priceFactor", 0)) if product_data.get("priceFactor") else None,
                "calculated_price": bool(safe_get_value(product_data, "calculatedPrice", False)),
                "definition_price_scope": safe_get_value(product_data, "definitionPriceScope", ""),
                
                # Dimensões e peso
                "height": float(safe_get_value(product_data, "height", 0)) if product_data.get("height") else None,
                "width": float(safe_get_value(product_data, "width", 0)) if product_data.get("width") else None,
                "length": float(safe_get_value(product_data, "length", 0)) if product_data.get("length") else None,
                "weight": float(safe_get_value(product_data, "weight", 0)) if product_data.get("weight") else None,
                
                # Estoque
                "stock_quantity": int(safe_get_value(product_data, "stockQuantity", 0)),
                "additional_time": int(safe_get_value(product_data, "additionalTime", 0)),
                
                # Informações técnicas
                "nbm_code": nbm_code,
                "origin_id": origin_id,
                "origin_name": origin_name,
                "gender": safe_get_value(product_data, "gender", ""),
                
                # Garantia
                "warranty_time": int(safe_get_value(product_data, "warrantyTime", 0)) if product_data.get("warrantyTime") else None,
                "warranty_text": safe_get_value(product_data, "warrantyText", ""),
                
                # URLs e mídia
                "video_url": safe_get_value(product_data, "videoUrl", ""),
                
                # Status
                "active": bool(safe_get_value(product_data, "active", True)),
                "available": bool(safe_get_value(product_data, "available", True)),
                "allow_automatic_sku_marketplace_creation": bool(safe_get_value(product_data, "allowAutomaticSkuMarketplaceCreation", False)),
                
                # Dados JSON
                "characteristics": safe_get_value(product_data, "characteristics", []),
                "images": safe_get_value(product_data, "images", []),
                "skus": safe_get_value(product_data, "skus", []),
                "variations": safe_get_value(product_data, "variations", {}),
                "category_data": category_data if isinstance(category_data, dict) else {},
                "brand_data": brand_data if isinstance(brand_data, dict) else {},
                
                # Extrair URL da imagem principal
                "main_image_url": "",
                
                # Status de sincronização
                "sync_status": "synced",
                "last_sync_date": datetime.now(),
            }
            
            # Extrair URL da imagem principal das images
            images = safe_get_value(product_data, "images", [])
            if images and isinstance(images, list):
                for image in images:
                    if isinstance(image, dict) and image.get("main", False):
                        product_fields["main_image_url"] = image.get("url", "")
                        break
                # Se não achou imagem principal, usar a primeira
                if not product_fields["main_image_url"] and images:
                    first_image = images[0]
                    if isinstance(first_image, dict):
                        product_fields["main_image_url"] = first_image.get("url", "")
            
            # Verifica se produto já existe
            existing_product = db.query(models.Product).filter(
                models.Product.anymarket_id == anymarket_id
            ).first()
            
            if existing_product:
                # Atualizar produto existente
                for field, value in product_fields.items():
                    if field != "anymarket_id":  # Não atualizar o ID
                        setattr(existing_product, field, value)
                existing_product.updated_at = datetime.now()
                logger.info(f"📦 Produto atualizado: {anymarket_id} - {product_fields['title']}")
            else:
                # Criar novo produto
                new_product = models.Product(**product_fields)
                db.add(new_product)
                logger.info(f"✨ Produto criado: {anymarket_id} - {product_fields['title']}")
        
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar produto {product_data.get('id')}: {e}")
            continue
    
    db.commit()

def save_orders_to_db_expanded(orders_data: List[Dict], db: Session):
    """Salva pedidos no banco de dados com TODOS os campos expandidos"""
    for order_data in orders_data:
        try:
            anymarket_id = str(safe_get_value(order_data, "id", ""))
            
            # Verifica se pedido já existe
            existing_order = db.query(models.Order).filter(
                models.Order.anymarket_id == anymarket_id
            ).first()
            
            # Extrair dados do cliente
            buyer_data = safe_get_value(order_data, "buyer", {})
            
            # Extrair endereços
            shipping_address = safe_get_value(order_data, "shippingAddress", {})
            billing_address = safe_get_value(order_data, "billingAddress", {})
            
            # Extrair dados de envio
            shipping_data = safe_get_value(order_data, "shipping", {})
            
            # Extrair dados de pagamento
            payments = safe_get_value(order_data, "payments", [])
            payment_method = payments[0].get("method", "") if payments else ""
            payment_status = payments[0].get("status", "") if payments else ""
            installments = payments[0].get("installments", 1) if payments else 1
            
            # Extrair dados de nota fiscal
            invoice_data = safe_get_value(order_data, "invoice", {})
            
            # Preparar dados do pedido
            order_fields = {
                "anymarket_id": anymarket_id,
                "marketplace": safe_get_value(order_data, "marketplace", ""),
                "marketplace_order_id": safe_get_value(order_data, "marketplaceOrderId", ""),
                "status": safe_get_value(order_data, "status", ""),
                "order_type": safe_get_value(order_data, "type", ""),
                
                # Valores financeiros
                "total_amount": float(safe_get_value(order_data, "totalAmount", 0)),
                "discount_amount": float(safe_get_value(order_data, "discountAmount", 0)),
                "shipping_amount": float(safe_get_value(order_data, "shippingAmount", 0)),
                "tax_amount": float(safe_get_value(order_data, "taxAmount", 0)),
                "products_amount": float(safe_get_value(order_data, "productsAmount", 0)),
                
                # Dados do cliente
                "customer_name": safe_get_value(buyer_data, "name", ""),
                "customer_email": safe_get_value(buyer_data, "email", ""),
                "customer_phone": safe_get_value(buyer_data, "phone", ""),
                "customer_document": safe_get_value(buyer_data, "document", ""),
                "customer_birth_date": parse_datetime(safe_get_value(buyer_data, "birthDate")),
                "customer_gender": safe_get_value(buyer_data, "gender", ""),
                
                # Informações de envio
                "shipping_method": safe_get_value(shipping_data, "method", ""),
                "shipping_company": safe_get_value(shipping_data, "company", ""),
                "tracking_number": safe_get_value(shipping_data, "trackingNumber", ""),
                "tracking_url": safe_get_value(shipping_data, "trackingUrl", ""),
                "estimated_delivery_date": parse_datetime(safe_get_value(shipping_data, "estimatedDeliveryDate")),
                "shipped_date": parse_datetime(safe_get_value(shipping_data, "shippedDate")),
                "delivered_date": parse_datetime(safe_get_value(shipping_data, "deliveredDate")),
                
                # Informações de pagamento
                "payment_method": payment_method,
                "payment_status": payment_status,
                "installments": installments,
                
                # Nota fiscal
                "invoice_number": safe_get_value(invoice_data, "number", ""),
                "invoice_series": safe_get_value(invoice_data, "series", ""),
                "invoice_access_key": safe_get_value(invoice_data, "accessKey", ""),
                "invoice_date": parse_datetime(safe_get_value(invoice_data, "date")),
                "invoice_cfop": safe_get_value(invoice_data, "cfop", ""),
                
                # Comentários
                "customer_comments": safe_get_value(order_data, "customerComments", ""),
                "internal_comments": safe_get_value(order_data, "internalComments", ""),
                "marketplace_comments": safe_get_value(order_data, "marketplaceComments", ""),
                "gift_message": safe_get_value(order_data, "giftMessage", ""),
                "is_gift": bool(safe_get_value(order_data, "isGift", False)),
                
                # Dados JSON
                "items_data": safe_get_value(order_data, "items", []),
                "payments_data": payments,
                "shipping_data": shipping_data,
                "marketplace_data": safe_get_value(order_data, "marketplaceData", {}),
                
                # Datas importantes
                "order_date": parse_datetime(safe_get_value(order_data, "createdAt")) or datetime.now(),
                "approved_date": parse_datetime(safe_get_value(order_data, "approvedAt")),
                "invoiced_date": parse_datetime(safe_get_value(order_data, "invoicedAt")),
                "canceled_date": parse_datetime(safe_get_value(order_data, "canceledAt")),
                
                # Status flags
                "is_canceled": bool(safe_get_value(order_data, "isCanceled", False)),
                "is_invoiced": bool(safe_get_value(order_data, "isInvoiced", False)),
                "is_shipped": bool(safe_get_value(order_data, "isShipped", False)),
                "is_delivered": bool(safe_get_value(order_data, "isDelivered", False)),
            }
            
            # Adicionar dados de endereço
            order_fields.update(extract_address_data(shipping_address, "shipping_address"))
            order_fields.update(extract_address_data(billing_address, "billing_address"))
            
            if existing_order:
                # Atualizar pedido existente
                for field, value in order_fields.items():
                    if field != "anymarket_id":  # Não atualizar o ID
                        setattr(existing_order, field, value)
                existing_order.updated_at = datetime.now()
                logger.info(f"📦 Order atualizado: {anymarket_id}")
            else:
                # Criar novo pedido
                new_order = models.Order(**order_fields)
                db.add(new_order)
                logger.info(f"✨ Order criado: {anymarket_id}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar order {order_data.get('id')}: {e}")
            continue
    
    db.commit()

@app.get("/")
def read_root():
    return {"message": "Anymarket Backend API - Versão 2.0 (Products + Orders Expandidos)"}

@app.post("/sync/products")
def sync_products(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos da API Anymarket com campos expandidos"""
    def sync_task():
        offset = 0
        limit = 50
        total_products = 0
        
        logger.info("🚀 Iniciando sincronização EXPANDIDA de produtos...")
        
        while True:
            logger.info(f"🔍 Buscando produtos: offset {offset}, limit {limit}")
            products_response = anymarket_client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                break
            
            save_products_to_db_expanded(products, db)
            total_products += len(products)
            offset += limit
            
            logger.info(f"📊 Total de produtos processados: {total_products}")
            
            # Se retornou menos que o limite, não há mais produtos
            if len(products) < limit:
                break
        
        logger.info(f"🎉 Sincronização de produtos concluída. Total: {total_products}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização EXPANDIDA de produtos iniciada"}

@app.post("/sync/orders")
def sync_orders(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza pedidos da API Anymarket com campos expandidos"""
    def sync_task():
        offset = 0
        limit = 50
        total_orders = 0
        
        logger.info("🚀 Iniciando sincronização EXPANDIDA de pedidos...")
        
        while True:
            logger.info(f"🔍 Buscando pedidos: offset {offset}, limit {limit}")
            orders_response = anymarket_client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                break
            
            save_orders_to_db_expanded(orders, db)
            total_orders += len(orders)
            offset += limit
            
            logger.info(f"📊 Total de pedidos processados: {total_orders}")
            
            # Se retornou menos que o limite, não há mais pedidos
            if len(orders) < limit:
                break
        
        logger.info(f"🎉 Sincronização de pedidos concluída. Total: {total_orders}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização EXPANDIDA de pedidos iniciada"}

@app.post("/sync/all")
def sync_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos E pedidos em paralelo"""
    def sync_all_task():
        logger.info("🚀 Iniciando sincronização COMPLETA (produtos + pedidos)...")
        
        # Sincronizar produtos primeiro
        offset = 0
        limit = 50
        total_products = 0
        
        logger.info("📦 Fase 1: Sincronizando produtos...")
        while True:
            products_response = anymarket_client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                break
            
            save_products_to_db_expanded(products, db)
            total_products += len(products)
            offset += limit
            
            if len(products) < limit:
                break
        
        logger.info(f"✅ Produtos sincronizados: {total_products}")
        
        # Sincronizar pedidos
        offset = 0
        total_orders = 0
        
        logger.info("📋 Fase 2: Sincronizando pedidos...")
        while True:
            orders_response = anymarket_client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                break
            
            save_orders_to_db_expanded(orders, db)
            total_orders += len(orders)
            offset += limit
            
            if len(orders) < limit:
                break
        
        logger.info(f"✅ Pedidos sincronizados: {total_orders}")
        logger.info(f"🎉 Sincronização COMPLETA finalizada! Produtos: {total_products}, Pedidos: {total_orders}")
    
    background_tasks.add_task(sync_all_task)
    return {"message": "Sincronização COMPLETA iniciada (produtos + pedidos)"}

# Endpoints para Products
@app.get("/products", response_model=List[schemas.ProductSummary])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista produtos do banco de dados (resumo)"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/full", response_model=List[schemas.Product])
def get_products_full(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista produtos do banco de dados (todos os campos)"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Busca um produto específico por ID"""
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product

@app.get("/products/anymarket/{anymarket_id}", response_model=schemas.Product)
def get_product_by_anymarket_id(anymarket_id: str, db: Session = Depends(get_db)):
    """Busca um produto específico por ID da Anymarket"""
    product = db.query(models.Product).filter(models.Product.anymarket_id == anymarket_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product

@app.get("/products/search/{search_term}")
def search_products(search_term: str, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """Busca produtos por termo (título, SKU, marca)"""
    products = db.query(models.Product).filter(
        models.Product.title.ilike(f"%{search_term}%") |
        models.Product.sku.ilike(f"%{search_term}%") |
        models.Product.brand_name.ilike(f"%{search_term}%")
    ).offset(skip).limit(limit).all()
    return products

# Endpoints para Orders
@app.get("/orders", response_model=List[schemas.OrderSummary])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista pedidos do banco de dados (resumo)"""
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/full", response_model=List[schemas.Order])
def get_orders_full(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista pedidos do banco de dados (todos os campos)"""
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Busca um pedido específico por ID"""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order

@app.get("/orders/anymarket/{anymarket_id}", response_model=schemas.Order)
def get_order_by_anymarket_id(anymarket_id: str, db: Session = Depends(get_db)):
    """Busca um pedido específico por ID da Anymarket"""
    order = db.query(models.Order).filter(models.Order.anymarket_id == anymarket_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order

# Endpoints de estatísticas
@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Estatísticas gerais do banco"""
    total_products = db.query(models.Product).count()
    total_orders = db.query(models.Order).count()
    active_products = db.query(models.Product).filter(models.Product.active == True).count()
    
    return {
        "products": {
            "total": total_products,
            "active": active_products,
            "inactive": total_products - active_products
        },
        "orders": {
            "total": total_orders
        }
    }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)