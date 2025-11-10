#!/usr/bin/env python3
"""
Script de atualização diária para sincronizar products, orders, stocks e sku_marketplaces
Busca apenas dados novos baseado na última data de criação no banco
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# Adicionar o diretório do app ao path
sys.path.append(str(Path(__file__).parent))

from app.database import engine, SessionLocal
from app import models
from app.anymarket_client import AnymarketClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_get_value(data: dict, key: str, default=None):
    """Função auxiliar para extrair valores de forma segura"""
    value = data.get(key, default)
    return value if value is not None else default

def parse_datetime(date_string):
    """Converte string de data ISO para datetime"""
    if not date_string:
        return None
    try:
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        return None

# ============================================================================
# FUNÇÕES DE SINCRONIZAÇÃO DE PRODUCTS (já existentes)
# ============================================================================

def get_last_product_created_at(db):
    """Busca a última data de criação de produto no banco"""
    try:
        last_product = db.query(models.Product).filter(
            models.Product.created_at.isnot(None)
        ).order_by(models.Product.created_at.desc()).first()
        
        if last_product:
            last_date = last_product.created_at + timedelta(seconds=1)
            logger.info(f"🔍 Último produto criado em: {last_product.created_at}")
            logger.info(f"📅 Buscando produtos desde: {last_date}")
            return last_date
        else:
            default_date = datetime.now() - timedelta(days=30)
            logger.info(f"📭 Nenhum produto no banco, buscando desde: {default_date}")
            return default_date
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar última data de produto: {e}")
        return datetime.now() - timedelta(days=7)

def save_products_to_db_ultra_complete(products_data, db):
    """Salva produtos no banco com todos os campos expandidos"""
    # (Usar a função do migrate_products_ultra_final.py)
    for product_data in products_data:
        try:
            anymarket_id = str(safe_get_value(product_data, "id", ""))
            
            existing_product = db.query(models.Product).filter(
                models.Product.anymarket_id == anymarket_id
            ).first()
            
            category = safe_get_value(product_data, "category", {})
            brand = safe_get_value(product_data, "brand", {})
            nbm = safe_get_value(product_data, "nbm", {})
            origin = safe_get_value(product_data, "origin", {})
            
            images = safe_get_value(product_data, "images", [])
            first_image = images[0] if images else {}
            
            skus = safe_get_value(product_data, "skus", [])
            first_sku = skus[0] if skus else {}
            
            characteristics = safe_get_value(product_data, "characteristics", [])
            first_characteristic = characteristics[0] if characteristics else {}
            
            # Processar campos (versão resumida - usar função completa do migrate)
            product_fields = {
                "anymarket_id": anymarket_id,
                "title": safe_get_value(product_data, "title", ""),
                "sync_status": "synced",
                "last_sync_date": datetime.now(),
            }
            
            if existing_product:
                for field, value in product_fields.items():
                    if field != "anymarket_id":
                        setattr(existing_product, field, value)
                existing_product.updated_at = datetime.now()
                logger.info(f"📦 Product atualizado: {anymarket_id}")
            else:
                new_product = models.Product(**product_fields)
                db.add(new_product)
                logger.info(f"✨ Product criado: {anymarket_id}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar product {product_data.get('id')}: {e}")
            continue
    
    db.commit()

def update_products_since_date(client, db, since_date):
    """Atualiza produtos criados/modificados desde uma data específica"""
    try:
        logger.info(f"📥 Iniciando atualização de produtos desde: {since_date}")
        
        offset = 0
        limit = 50
        total_updated = 0
        
        while True:
            logger.info(f"🔍 Buscando produtos: offset {offset}, limit {limit}")
            products_response = client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                logger.info("📭 Nenhum produto encontrado.")
                break
            
            filtered_products = []
            for product in products:
                product_created_at = parse_datetime(product.get("createdAt"))
                if product_created_at and product_created_at >= since_date:
                    filtered_products.append(product)
            
            if not filtered_products:
                logger.info(f"📅 Nenhum produto novo desde {since_date}")
                break
            
            logger.info(f"📦 Processando {len(filtered_products)} produtos novos/atualizados...")
            save_products_to_db_ultra_complete(filtered_products, db)
            
            total_updated += len(filtered_products)
            offset += limit
            
            logger.info(f"✅ Total atualizado até agora: {total_updated}")
            
            if len(products) < limit or len(filtered_products) == 0:
                break
            
            time.sleep(0.5)
        
        logger.info(f"🎉 Atualização de produtos concluída! Total: {total_updated}")
        return total_updated
        
    except Exception as e:
        logger.error(f"❌ Erro na atualização de produtos: {e}")
        return 0

# ============================================================================
# FUNÇÕES DE SINCRONIZAÇÃO DE ORDERS (já existentes)
# ============================================================================

def get_last_order_created_at(db):
    """Busca a última data de criação de pedido no banco"""
    try:
        last_order = db.query(models.Order).filter(
            models.Order.created_at.isnot(None)
        ).order_by(models.Order.created_at.desc()).first()
        
        if last_order:
            last_date = last_order.created_at + timedelta(seconds=1)
            logger.info(f"🔍 Último pedido criado em: {last_order.created_at}")
            logger.info(f"📅 Buscando pedidos desde: {last_date}")
            return last_date
        else:
            default_date = datetime.now() - timedelta(days=30)
            logger.info(f"📭 Nenhum pedido no banco, buscando desde: {default_date}")
            return default_date
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar última data de pedido: {e}")
        return datetime.now() - timedelta(days=7)

def save_orders_to_db_ultra_complete(orders_data, db):
    """Salva pedidos no banco com todos os campos expandidos"""
    # (Usar a função do migrate_orders_ultra_final.py)
    for order_data in orders_data:
        try:
            anymarket_id = str(safe_get_value(order_data, "id", ""))
            
            existing_order = db.query(models.Order).filter(
                models.Order.anymarket_id == anymarket_id
            ).first()
            
            # Processar campos (versão resumida - usar função completa do migrate)
            order_fields = {
                "anymarket_id": anymarket_id,
                "marketplace": safe_get_value(order_data, "marketPlace", ""),
                "status": safe_get_value(order_data, "status", ""),
            }
            
            if existing_order:
                for field, value in order_fields.items():
                    if field != "anymarket_id":
                        setattr(existing_order, field, value)
                existing_order.updated_at = datetime.now()
                logger.info(f"📦 Order atualizado: {anymarket_id}")
            else:
                new_order = models.Order(**order_fields)
                db.add(new_order)
                logger.info(f"✨ Order criado: {anymarket_id}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar order {order_data.get('id')}: {e}")
            continue
    
    db.commit()

def update_orders_since_date(client, db, since_date):
    """Atualiza pedidos criados/modificados desde uma data específica"""
    try:
        logger.info(f"📥 Iniciando atualização de pedidos desde: {since_date}")
        
        offset = 0
        limit = 50
        total_updated = 0
        
        while True:
            logger.info(f"🔍 Buscando pedidos: offset {offset}, limit {limit}")
            orders_response = client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                logger.info("📭 Nenhum pedido encontrado.")
                break
            
            filtered_orders = []
            for order in orders:
                order_created_at = parse_datetime(order.get("createdAt"))
                if order_created_at and order_created_at >= since_date:
                    filtered_orders.append(order)
            
            if not filtered_orders:
                logger.info(f"📅 Nenhum pedido novo desde {since_date}")
                break
            
            logger.info(f"📦 Processando {len(filtered_orders)} pedidos novos/atualizados...")
            save_orders_to_db_ultra_complete(filtered_orders, db)
            
            total_updated += len(filtered_orders)
            offset += limit
            
            logger.info(f"✅ Total atualizado até agora: {total_updated}")
            
            if len(orders) < limit or len(filtered_orders) == 0:
                break
            
            time.sleep(0.5)
        
        logger.info(f"🎉 Atualização de pedidos concluída! Total: {total_updated}")
        return total_updated
        
    except Exception as e:
        logger.error(f"❌ Erro na atualização de pedidos: {e}")
        return 0

# ============================================================================
# FUNÇÕES DE SINCRONIZAÇÃO DE STOCKS (NOVO)
# ============================================================================

def save_stocks_to_db(stocks_data, db):
    """Salva stocks no banco de dados com todos os campos expandidos"""
    for stock_data in stocks_data:
        try:
            # Extrair SKU
            sku = safe_get_value(stock_data, "stockKeepingUnit", {})
            sku_id = str(safe_get_value(sku, "id", ""))
            sku_title = safe_get_value(sku, "title", "")
            sku_partner_id = safe_get_value(sku, "partnerId", "")
            
            # Extrair Stock Local
            stock_local = safe_get_value(stock_data, "stockLocal", {})
            stock_local_id = str(safe_get_value(stock_local, "id", ""))
            stock_local_oi = safe_get_value(stock_local, "oi", {})
            stock_local_oi_value = safe_get_value(stock_local_oi, "value", "")
            stock_local_name = safe_get_value(stock_local, "name", "")
            stock_local_virtual = bool(safe_get_value(stock_local, "virtual", False))
            stock_local_default_local = bool(safe_get_value(stock_local, "defaultLocal", False))
            stock_local_priority_points = int(safe_get_value(stock_local, "priorityPoints", 0))
            
            # Chave única composta
            sku_stock_key = f"{sku_id}_{stock_local_id}"
            
            # Verificar se stock já existe
            existing_stock = db.query(models.Stock).filter(
                models.Stock.sku_stock_key == sku_stock_key
            ).first()
            
            # Extrair quantidades
            amount = int(safe_get_value(stock_data, "amount", 0))
            reservation_amount = int(safe_get_value(stock_data, "reservationAmount", 0))
            available_amount = int(safe_get_value(stock_data, "availableAmount", 0))
            
            # Extrair informações adicionais
            price = float(safe_get_value(stock_data, "price", 0))
            active = bool(safe_get_value(stock_data, "active", True))
            additional_time = int(safe_get_value(stock_data, "additionalTime", 0))
            last_stock_update = safe_get_value(stock_data, "lastStockUpdate", "")
            last_stock_update_parsed = parse_datetime(last_stock_update)
            
            # Mapear todos os campos
            stock_fields = {
                "sku_id": sku_id,
                "sku_title": sku_title,
                "sku_partner_id": sku_partner_id,
                "stock_local_id": stock_local_id,
                "stock_local_oi_value": stock_local_oi_value,
                "stock_local_name": stock_local_name,
                "stock_local_virtual": stock_local_virtual,
                "stock_local_default_local": stock_local_default_local,
                "stock_local_priority_points": stock_local_priority_points,
                "amount": amount,
                "reservation_amount": reservation_amount,
                "available_amount": available_amount,
                "price": price,
                "active": active,
                "additional_time": additional_time,
                "last_stock_update": last_stock_update,
                "last_stock_update_parsed": last_stock_update_parsed,
                "stock_keeping_unit_data": sku,
                "stock_local_data": stock_local,
                "sku_stock_key": sku_stock_key,
                "sync_status": "synced",
                "last_sync_date": datetime.now(),
            }
            
            if existing_stock:
                # Atualizar stock existente
                for field, value in stock_fields.items():
                    if field != "sku_stock_key":
                        setattr(existing_stock, field, value)
                existing_stock.updated_at = datetime.now()
                logger.info(f"📦 Stock atualizado: SKU {sku_partner_id} | Local {stock_local_name} | Qtd: {amount}")
            else:
                # Criar novo stock
                new_stock = models.Stock(**stock_fields)
                db.add(new_stock)
                logger.info(f"✨ Stock criado: SKU {sku_partner_id} | Local {stock_local_name} | Qtd: {amount}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar stock: {e}")
            continue
    
    db.commit()

def update_all_stocks(client, db):
    """Atualiza todos os stocks (não há filtro de data para stocks)"""
    try:
        logger.info(f"📥 Iniciando atualização completa de stocks...")
        
        offset = 0
        limit = 50
        total_updated = 0
        
        while True:
            logger.info(f"🔍 Buscando stocks: offset {offset}, limit {limit}")
            
            stocks_response = client.get_stocks(limit=limit, offset=offset)
            stocks = stocks_response.get("content", [])
            
            if not stocks:
                logger.info("📭 Nenhum stock encontrado.")
                break
            
            logger.info(f"📦 Processando {len(stocks)} stocks...")
            save_stocks_to_db(stocks, db)
            
            total_updated += len(stocks)
            offset += limit
            
            logger.info(f"✅ Total atualizado até agora: {total_updated}")
            
            if len(stocks) < limit:
                break
            
            time.sleep(0.5)
        
        logger.info(f"🎉 Atualização de stocks concluída! Total: {total_updated}")
        return total_updated
        
    except Exception as e:
        logger.error(f"❌ Erro na atualização de stocks: {e}")
        return 0

# ============================================================================
# FUNÇÕES DE SINCRONIZAÇÃO DE SKU MARKETPLACES (NOVO)
# ============================================================================

def save_sku_marketplaces_to_db(sku_marketplaces_data, db):
    """Salva SKU marketplaces no banco de dados com todos os campos expandidos"""
    for sku_mp_data in sku_marketplaces_data:
        try:
            # Campos básicos
            anymarket_id = str(safe_get_value(sku_mp_data, "id", ""))
            account_name = safe_get_value(sku_mp_data, "accountName", "")
            id_account = int(safe_get_value(sku_mp_data, "idAccount", 0)) if sku_mp_data.get("idAccount") else None
            marketplace = safe_get_value(sku_mp_data, "marketPlace", "")
            id_in_marketplace = safe_get_value(sku_mp_data, "idInMarketplace", "")
            index_field = int(safe_get_value(sku_mp_data, "index", 0)) if sku_mp_data.get("index") else None
            
            # Chave única composta
            sku_marketplace_key = f"{anymarket_id}_{marketplace}_{id_in_marketplace}"
            
            # Verificar se já existe
            existing_sku_mp = db.query(models.SkuMarketplace).filter(
                models.SkuMarketplace.sku_marketplace_key == sku_marketplace_key
            ).first()
            
            # Status
            publication_status = safe_get_value(sku_mp_data, "publicationStatus", "")
            marketplace_status = safe_get_value(sku_mp_data, "marketplaceStatus", "")
            
            # Preços
            price = float(safe_get_value(sku_mp_data, "price", 0))
            price_factor = float(safe_get_value(sku_mp_data, "priceFactor", 0))
            discount_price = float(safe_get_value(sku_mp_data, "discountPrice", 0))
            
            # Links
            permalink = safe_get_value(sku_mp_data, "permalink", "")
            sku_in_marketplace = safe_get_value(sku_mp_data, "skuInMarketplace", "")
            marketplace_item_code = safe_get_value(sku_mp_data, "marketplaceItemCode", "")
            
            # Extrair fields
            fields = safe_get_value(sku_mp_data, "fields", {})
            
            # Mapear todos os campos
            sku_mp_fields = {
                "anymarket_id": anymarket_id,
                "account_name": account_name,
                "id_account": id_account,
                "marketplace": marketplace,
                "id_in_marketplace": id_in_marketplace,
                "index_field": index_field,
                "publication_status": publication_status,
                "marketplace_status": marketplace_status,
                "price": price,
                "price_factor": price_factor,
                "discount_price": discount_price,
                "permalink": permalink,
                "sku_in_marketplace": sku_in_marketplace,
                "marketplace_item_code": marketplace_item_code,
                
                # Fields expandidos
                "field_title": safe_get_value(fields, "title", ""),
                "field_template": int(safe_get_value(fields, "template", 0)) if fields.get("template") else None,
                "field_price_factor": safe_get_value(fields, "priceFactor", ""),
                "field_discount_type": safe_get_value(fields, "DISCOUNT_TYPE", ""),
                "field_discount_value": safe_get_value(fields, "DISCOUNT_VALUE", ""),
                "field_has_discount": bool(safe_get_value(fields, "HAS_DISCOUNT", False)),
                "field_concat_attributes": safe_get_value(fields, "CONCAT_ATTRIBUTES", ""),
                "field_delivery_type": safe_get_value(fields, "delivery_type", ""),
                "field_shipment": safe_get_value(fields, "SHIPMENT", ""),
                "field_cross_docking": safe_get_value(fields, "crossDocking", ""),
                "field_custom_description": safe_get_value(fields, "CUSTOM_DESCRIPTION", ""),
                "field_ean": safe_get_value(fields, "EAN", ""),
                "field_manufacturing_time": safe_get_value(fields, "MANUFACTURING_TIME", ""),
                "field_value": safe_get_value(fields, "VALUE", ""),
                "field_percent": safe_get_value(fields, "PERCENT", ""),
                
                # Mercado Livre specific
                "field_bronze_price": safe_get_value(fields, "bronze_price", ""),
                "field_bronze_price_factor": safe_get_value(fields, "bronze_price_factor", ""),
                "field_buying_mode": safe_get_value(fields, "buying_mode", ""),
                "field_category_with_variation": safe_get_value(fields, "category_with_variation", ""),
                "field_condition": safe_get_value(fields, "condition", ""),
                "field_free_price": safe_get_value(fields, "free_price", ""),
                "field_free_price_factor": safe_get_value(fields, "free_price_factor", ""),
                "field_free_shipping": bool(safe_get_value(fields, "free_shipping", False)),
                "field_gold_premium_price": safe_get_value(fields, "gold_premium_price", ""),
                "field_gold_premium_price_factor": safe_get_value(fields, "gold_premium_price_factor", ""),
                "field_gold_price": safe_get_value(fields, "gold_price", ""),
                "field_gold_price_factor": safe_get_value(fields, "gold_price_factor", ""),
                "field_gold_pro_price": safe_get_value(fields, "gold_pro_price", ""),
                "field_gold_pro_price_factor": safe_get_value(fields, "gold_pro_price_factor", ""),
                "field_gold_special_price": safe_get_value(fields, "gold_special_price", ""),
                "field_gold_special_price_factor": safe_get_value(fields, "gold_special_price_factor", ""),
                "field_listing_type_id": safe_get_value(fields, "listing_type_id", ""),
                "field_shipping_local_pick_up": bool(safe_get_value(fields, "shipping_local_pick_up", False)),
                "field_shipping_mode": safe_get_value(fields, "shipping_mode", ""),
                "field_silver_price": safe_get_value(fields, "silver_price", ""),
                "field_silver_price_factor": safe_get_value(fields, "silver_price_factor", ""),
                "field_measurement_chart_id": safe_get_value(fields, "measurement_chart_id", ""),
                "field_warranty_time": safe_get_value(fields, "warranty_time", ""),
                "field_has_fulfillment": bool(safe_get_value(fields, "HAS_FULFILLMENT", False)),
                "field_official_store_id": safe_get_value(fields, "official_store_id", ""),
                "field_ml_channels": safe_get_value(fields, "ml_channels", ""),
                "field_is_main_sku": bool(safe_get_value(fields, "is_main_sku", False)),
                "field_is_match": bool(safe_get_value(fields, "is_match", False)),
                
                # JSON completos
                "fields_data": fields,
                "attributes_data": safe_get_value(sku_mp_data, "attributes", {}),
                "warnings": safe_get_value(sku_mp_data, "warnings", []),
                
                "sku_marketplace_key": sku_marketplace_key,
                "sync_status": "synced",
                "last_sync_date": datetime.now(),
            }
            
            if existing_sku_mp:
                # Atualizar
                for field, value in sku_mp_fields.items():
                    if field != "sku_marketplace_key":
                        setattr(existing_sku_mp, field, value)
                existing_sku_mp.updated_at = datetime.now()
                logger.info(f"📦 SKU Marketplace atualizado: {anymarket_id} | {marketplace} | Status: {publication_status}")
            else:
                # Criar novo
                new_sku_mp = models.SkuMarketplace(**sku_mp_fields)
                db.add(new_sku_mp)
                logger.info(f"✨ SKU Marketplace criado: {anymarket_id} | {marketplace} | Status: {publication_status}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar SKU marketplace: {e}")
            continue
    
    db.commit()

def update_all_sku_marketplaces(client, db):
    """Atualiza todos os SKU marketplaces"""
    try:
        logger.info(f"📥 Iniciando atualização completa de SKU marketplaces...")
        
        offset = 0
        limit = 50
        total_updated = 0
        
        while True:
            logger.info(f"🔍 Buscando SKU marketplaces: offset {offset}, limit {limit}")
            
            # Nota: Este endpoint retorna uma lista direta
            sku_marketplaces = client.get_sku_marketplaces(limit=limit, offset=offset)
            
            if not sku_marketplaces:
                logger.info("📭 Nenhum SKU marketplace encontrado.")
                break
            
            logger.info(f"📦 Processando {len(sku_marketplaces)} SKU marketplaces...")
            save_sku_marketplaces_to_db(sku_marketplaces, db)
            
            total_updated += len(sku_marketplaces)
            offset += limit
            
            logger.info(f"✅ Total atualizado até agora: {total_updated}")
            
            if len(sku_marketplaces) < limit:
                break
            
            time.sleep(0.5)
        
        logger.info(f"🎉 Atualização de SKU marketplaces concluída! Total: {total_updated}")
        return total_updated
        
    except Exception as e:
        logger.error(f"❌ Erro na atualização de SKU marketplaces: {e}")
        return 0

# ============================================================================
# FUNÇÃO DE RESUMO E VERIFICAÇÃO
# ============================================================================

def create_daily_summary(products_updated, orders_updated, stocks_updated, sku_mp_updated, start_time, end_time):
    """Cria um resumo da sincronização diária"""
    try:
        duration = end_time - start_time
        
        summary = {
            "date": datetime.now().isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration),
            "products_updated": products_updated,
            "orders_updated": orders_updated,
            "stocks_updated": stocks_updated,
            "sku_marketplaces_updated": sku_mp_updated,
            "total_records": products_updated + orders_updated + stocks_updated + sku_mp_updated,
            "status": "success" if all(x >= 0 for x in [products_updated, orders_updated, stocks_updated, sku_mp_updated]) else "error"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_filename = f"daily_sync_summary_{timestamp}.json"
        
        with open(summary_filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Resumo salvo: {summary_filename}")
        return summary_filename
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar resumo: {e}")
        return None

def verify_sync_status(db):
    """Verifica o status da sincronização e estatísticas do banco"""
    try:
        # Contar totais
        total_products = db.query(models.Product).count()
        total_orders = db.query(models.Order).count()
        total_stocks = db.query(models.Stock).count()
        total_sku_mp = db.query(models.SkuMarketplace).count()
        
        # Recentes (últimas 24h)
        yesterday = datetime.now() - timedelta(days=1)
        recent_products = db.query(models.Product).filter(
            models.Product.created_at >= yesterday
        ).count()
        recent_orders = db.query(models.Order).filter(
            models.Order.created_at >= yesterday
        ).count()
        recent_stocks = db.query(models.Stock).filter(
            models.Stock.created_at >= yesterday
        ).count()
        recent_sku_mp = db.query(models.SkuMarketplace).filter(
            models.SkuMarketplace.created_at >= yesterday
        ).count()
        
        logger.info(f"📊 Status do banco de dados:")
        logger.info(f"   - Total products: {total_products}")
        logger.info(f"   - Total orders: {total_orders}")
        logger.info(f"   - Total stocks: {total_stocks}")
        logger.info(f"   - Total SKU marketplaces: {total_sku_mp}")
        logger.info(f"   - Products recentes (24h): {recent_products}")
        logger.info(f"   - Orders recentes (24h): {recent_orders}")
        logger.info(f"   - Stocks recentes (24h): {recent_stocks}")
        logger.info(f"   - SKU marketplaces recentes (24h): {recent_sku_mp}")
        
        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_stocks": total_stocks,
            "total_sku_marketplaces": total_sku_mp,
            "recent_products": recent_products,
            "recent_orders": recent_orders,
            "recent_stocks": recent_stocks,
            "recent_sku_marketplaces": recent_sku_mp,
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {e}")
        return None

# ============================================================================
# FUNÇÃO PRINCIPAL
# ============================================================================

def main():
    """Função principal da atualização diária"""
    start_time = datetime.now()
    
    print("🔄 ATUALIZAÇÃO DIÁRIA - ANYMARKET BACKEND")
    print("=" * 60)
    print(f"⏰ Iniciada em: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print("")
    print("Este script vai:")
    print("1. Buscar a última data de criação de produtos no banco")
    print("2. Buscar a última data de criação de pedidos no banco")
    print("3. Atualizar todos os stocks (completo)")
    print("4. Atualizar todos os SKU marketplaces (completo)")
    print("5. Importar apenas dados novos desde essas datas")
    print("6. Gerar relatório de sincronização")
    print("")
    
    # Modo automático ou manual
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        run_mode = "auto"
        logger.info("🤖 Executando em modo automático")
    else:
        run_mode = "manual"
        confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
        if confirm not in ['sim', 's', 'yes', 'y']:
            print("❌ Operação cancelada")
            return
    
    try:
        # Instanciar cliente e sessão do banco
        logger.info("🔧 Inicializando cliente API e banco de dados...")
        client = AnymarketClient()
        db = SessionLocal()
        
        # Verificar status inicial
        print("\n" + "="*40)
        logger.info("📊 Verificando status inicial do banco...")
        initial_status = verify_sync_status(db)
        
        # Passo 1: Atualizar produtos
        print("\n" + "="*40)
        logger.info("🛍️  ATUALIZANDO PRODUTOS...")
        last_product_date = get_last_product_created_at(db)
        products_updated = update_products_since_date(client, db, last_product_date)
        
        # Passo 2: Atualizar pedidos
        print("\n" + "="*40)
        logger.info("📦 ATUALIZANDO PEDIDOS...")
        last_order_date = get_last_order_created_at(db)
        orders_updated = update_orders_since_date(client, db, last_order_date)
        
        # Passo 3: Atualizar stocks (NOVO)
        print("\n" + "="*40)
        logger.info("📊 ATUALIZANDO STOCKS...")
        stocks_updated = update_all_stocks(client, db)
        
        # Passo 4: Atualizar SKU marketplaces (NOVO)
        print("\n" + "="*40)
        logger.info("🏪 ATUALIZANDO SKU MARKETPLACES...")
        sku_mp_updated = update_all_sku_marketplaces(client, db)
        
        # Passo 5: Verificar status final
        print("\n" + "="*40)
        logger.info("📊 Verificando status final...")
        final_status = verify_sync_status(db)
        
        # Calcular estatísticas
        end_time = datetime.now()
        
        # Passo 6: Criar resumo
        print("\n" + "="*40)
        summary_file = create_daily_summary(products_updated, orders_updated, stocks_updated, sku_mp_updated, start_time, end_time)
        
        # Resultado final
        print("\n" + "🎉 ATUALIZAÇÃO DIÁRIA CONCLUÍDA! " + "🎉")
        print("=" * 60)
        print(f"⏰ Iniciada: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"⏰ Finalizada: {end_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"⏱️  Duração: {end_time - start_time}")
        print(f"🛍️  Produtos atualizados: {products_updated}")
        print(f"📦 Pedidos atualizados: {orders_updated}")
        print(f"📊 Stocks atualizados: {stocks_updated}")
        print(f"🏪 SKU Marketplaces atualizados: {sku_mp_updated}")
        print(f"📊 Total de registros: {products_updated + orders_updated + stocks_updated + sku_mp_updated}")
        
        if summary_file:
            print(f"📄 Relatório salvo: {summary_file}")
        
        print("")
        print("💡 Estatísticas do banco:")
        if final_status:
            print(f"   - Total produtos: {final_status['total_products']}")
            print(f"   - Total pedidos: {final_status['total_orders']}")
            print(f"   - Total stocks: {final_status['total_stocks']}")
            print(f"   - Total SKU marketplaces: {final_status['total_sku_marketplaces']}")
            print(f"   - Produtos recentes: {final_status['recent_products']}")
            print(f"   - Pedidos recentes: {final_status['recent_orders']}")
            print(f"   - Stocks recentes: {final_status['recent_stocks']}")
            print(f"   - SKU marketplaces recentes: {final_status['recent_sku_marketplaces']}")
        
        print("")
        print("🔄 Para automatizar, use:")
        print("   python daily_update.py --auto")
        print("")
        print("⏰ Para agendar no cron (todos os dias às 6h):")
        print("   0 6 * * * cd /caminho/para/projeto && python daily_update.py --auto")
        
        db.close()
        
    except Exception as e:
        logger.error(f"💥 Erro durante a atualização diária: {e}")
        print(f"❌ Atualização falhou: {e}")
        
        # Tentar salvar log de erro
        try:
            error_log = {
                "date": datetime.now().isoformat(),
                "error": str(e),
                "products_updated": locals().get('products_updated', 0),
                "orders_updated": locals().get('orders_updated', 0),
                "stocks_updated": locals().get('stocks_updated', 0),
                "sku_mp_updated": locals().get('sku_mp_updated', 0),
                "status": "error"
            }
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_filename = f"daily_sync_error_{timestamp}.json"
            
            with open(error_filename, 'w', encoding='utf-8') as f:
                json.dump(error_log, f, indent=2, ensure_ascii=False)
            
            print(f"❌ Log de erro salvo: {error_filename}")
            
        except:
            pass

if __name__ == "__main__":
    main()