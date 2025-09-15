#!/usr/bin/env python3
"""
Script de atualização diária para sincronizar products e orders
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

def get_last_product_created_at(db):
    """Busca a última data de criação de produto no banco"""
    try:
        last_product = db.query(models.Product).filter(
            models.Product.created_at.isnot(None)
        ).order_by(models.Product.created_at.desc()).first()
        
        if last_product:
            # Adicionar 1 segundo para evitar duplicatas
            last_date = last_product.created_at + timedelta(seconds=1)
            logger.info(f"🔍 Último produto criado em: {last_product.created_at}")
            logger.info(f"📅 Buscando produtos desde: {last_date}")
            return last_date
        else:
            # Se não há produtos, buscar dos últimos 30 dias
            default_date = datetime.now() - timedelta(days=30)
            logger.info(f"📭 Nenhum produto no banco, buscando desde: {default_date}")
            return default_date
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar última data de produto: {e}")
        # Em caso de erro, buscar dos últimos 7 dias
        return datetime.now() - timedelta(days=7)

def get_last_order_created_at(db):
    """Busca a última data de criação de pedido no banco"""
    try:
        last_order = db.query(models.Order).filter(
            models.Order.created_at.isnot(None)
        ).order_by(models.Order.created_at.desc()).first()
        
        if last_order:
            # Adicionar 1 segundo para evitar duplicatas
            last_date = last_order.created_at + timedelta(seconds=1)
            logger.info(f"🔍 Último pedido criado em: {last_order.created_at}")
            logger.info(f"📅 Buscando pedidos desde: {last_date}")
            return last_date
        else:
            # Se não há pedidos, buscar dos últimos 30 dias
            default_date = datetime.now() - timedelta(days=30)
            logger.info(f"📭 Nenhum pedido no banco, buscando desde: {default_date}")
            return default_date
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar última data de pedido: {e}")
        # Em caso de erro, buscar dos últimos 7 dias
        return datetime.now() - timedelta(days=7)

def save_products_to_db_ultra_complete(products_data, db):
    """
    Salva produtos no banco de dados com TODOS os campos expandidos
    Função copiada do migrate_products_ultra_final.py
    """
    for product_data in products_data:
        try:
            anymarket_id = str(safe_get_value(product_data, "id", ""))
            
            # Verifica se produto já existe
            existing_product = db.query(models.Product).filter(
                models.Product.anymarket_id == anymarket_id
            ).first()
            
            # Extrair objetos aninhados
            category = safe_get_value(product_data, "category", {})
            brand = safe_get_value(product_data, "brand", {})
            nbm = safe_get_value(product_data, "nbm", {})
            origin = safe_get_value(product_data, "origin", {})
            
            # EXTRAIR E EXPANDIR IMAGES_DATA
            images = safe_get_value(product_data, "images", [])
            first_image = images[0] if images else {}
            
            image_id = str(safe_get_value(first_image, "id", ""))
            image_index = int(safe_get_value(first_image, "index", 0)) if first_image.get("index") else None
            image_main = bool(safe_get_value(first_image, "main", False))
            image_url = safe_get_value(first_image, "url", "")
            image_thumbnail_url = safe_get_value(first_image, "thumbnailUrl", "")
            image_low_resolution_url = safe_get_value(first_image, "lowResolutionUrl", "")
            image_standard_url = safe_get_value(first_image, "standardUrl", "")
            image_original_image = safe_get_value(first_image, "originalImage", "")
            image_status = safe_get_value(first_image, "status", "")
            image_standard_width = int(safe_get_value(first_image, "standardWidth", 0)) if first_image.get("standardWidth") else None
            image_standard_height = int(safe_get_value(first_image, "standardHeight", 0)) if first_image.get("standardHeight") else None
            image_original_width = int(safe_get_value(first_image, "originalWidth", 0)) if first_image.get("originalWidth") else None
            image_original_height = int(safe_get_value(first_image, "originalHeight", 0)) if first_image.get("originalHeight") else None
            image_product_id = str(safe_get_value(first_image, "productId", ""))
            
            total_images = len(images)
            has_main_image = any(img.get("main", False) for img in images)
            main_image_url = ""
            
            for img in images:
                if img.get("main", False):
                    main_image_url = img.get("url", "")
                    break
            if not main_image_url and images:
                main_image_url = images[0].get("url", "")
            
            # EXTRAIR E EXPANDIR SKUS_DATA
            skus = safe_get_value(product_data, "skus", [])
            first_sku = skus[0] if skus else {}
            
            sku_id = str(safe_get_value(first_sku, "id", ""))
            sku_title = safe_get_value(first_sku, "title", "")
            sku_partner_id = safe_get_value(first_sku, "partnerId", "")
            sku_ean = safe_get_value(first_sku, "ean", "")
            sku_price = float(safe_get_value(first_sku, "price", 0))
            sku_amount = int(safe_get_value(first_sku, "amount", 0))
            sku_additional_time = int(safe_get_value(first_sku, "additionalTime", 0))
            sku_stock_local_id = str(safe_get_value(first_sku, "stockLocalId", ""))
            
            total_skus = len(skus)
            min_price = None
            max_price = None
            total_stock = 0
            avg_price = None
            has_stock = False
            
            if skus:
                prices = [float(sku.get("price", 0)) for sku in skus if sku.get("price")]
                amounts = [int(sku.get("amount", 0)) for sku in skus if sku.get("amount")]
                
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    avg_price = sum(prices) / len(prices)
                
                if amounts:
                    total_stock = sum(amounts)
                    has_stock = total_stock > 0
            
            # EXTRAIR E EXPANDIR CHARACTERISTICS_DATA
            characteristics = safe_get_value(product_data, "characteristics", [])
            first_characteristic = characteristics[0] if characteristics else {}
            
            characteristic_index = int(safe_get_value(first_characteristic, "index", 0)) if first_characteristic.get("index") else None
            characteristic_name = safe_get_value(first_characteristic, "name", "")
            characteristic_value = safe_get_value(first_characteristic, "value", "")
            total_characteristics = len(characteristics)
            has_characteristics = total_characteristics > 0
            
            # MAPEAR TODOS OS CAMPOS
            product_fields = {
                "anymarket_id": anymarket_id,
                "title": safe_get_value(product_data, "title", ""),
                "description": safe_get_value(product_data, "description", ""),
                "external_id_product": safe_get_value(product_data, "externalIdProduct", ""),
                
                "category_id": str(safe_get_value(category, "id", "")),
                "category_name": safe_get_value(category, "name", ""),
                "category_path": safe_get_value(category, "path", ""),
                
                "brand_id": str(safe_get_value(brand, "id", "")),
                "brand_name": safe_get_value(brand, "name", ""),
                "brand_reduced_name": safe_get_value(brand, "reducedName", ""),
                "brand_partner_id": safe_get_value(brand, "partnerId", ""),
                
                "nbm_id": safe_get_value(nbm, "id", ""),
                "nbm_description": safe_get_value(nbm, "description", ""),
                
                "origin_id": str(safe_get_value(origin, "id", "")),
                "origin_description": safe_get_value(origin, "description", ""),
                
                "model": safe_get_value(product_data, "model", ""),
                "video_url": safe_get_value(product_data, "videoUrl", ""),
                "gender": safe_get_value(product_data, "gender", ""),
                
                "warranty_time": int(safe_get_value(product_data, "warrantyTime", 0)) if product_data.get("warrantyTime") else None,
                "warranty_text": safe_get_value(product_data, "warrantyText", ""),
                
                "height": float(safe_get_value(product_data, "height", 0)) if product_data.get("height") else None,
                "width": float(safe_get_value(product_data, "width", 0)) if product_data.get("width") else None,
                "weight": float(safe_get_value(product_data, "weight", 0)) if product_data.get("weight") else None,
                "length": float(safe_get_value(product_data, "length", 0)) if product_data.get("length") else None,
                
                "price_factor": float(safe_get_value(product_data, "priceFactor", 0)) if product_data.get("priceFactor") else None,
                "calculated_price": bool(safe_get_value(product_data, "calculatedPrice", False)),
                "definition_price_scope": safe_get_value(product_data, "definitionPriceScope", ""),
                
                "has_variations": bool(safe_get_value(product_data, "hasVariations", False)),
                "is_product_active": bool(safe_get_value(product_data, "isProductActive", True)),
                "product_type": safe_get_value(product_data, "type", ""),
                "allow_automatic_sku_marketplace_creation": bool(safe_get_value(product_data, "allowAutomaticSkuMarketplaceCreation", True)),
                
                # IMAGES expandidas
                "image_id": image_id,
                "image_index": image_index,
                "image_main": image_main,
                "image_url": image_url,
                "image_thumbnail_url": image_thumbnail_url,
                "image_low_resolution_url": image_low_resolution_url,
                "image_standard_url": image_standard_url,
                "image_original_image": image_original_image,
                "image_status": image_status,
                "image_standard_width": image_standard_width,
                "image_standard_height": image_standard_height,
                "image_original_width": image_original_width,
                "image_original_height": image_original_height,
                "image_product_id": image_product_id,
                "total_images": total_images,
                "has_main_image": has_main_image,
                "main_image_url": main_image_url,
                
                # SKUS expandidos
                "sku_id": sku_id,
                "sku_title": sku_title,
                "sku_partner_id": sku_partner_id,
                "sku_ean": sku_ean,
                "sku_price": sku_price,
                "sku_amount": sku_amount,
                "sku_additional_time": sku_additional_time,
                "sku_stock_local_id": sku_stock_local_id,
                "total_skus": total_skus,
                "min_price": min_price,
                "max_price": max_price,
                "total_stock": total_stock,
                "avg_price": avg_price,
                "has_stock": has_stock,
                
                # CHARACTERISTICS expandidas
                "characteristic_index": characteristic_index,
                "characteristic_name": characteristic_name,
                "characteristic_value": characteristic_value,
                "total_characteristics": total_characteristics,
                "has_characteristics": has_characteristics,
                
                # Campos legados
                "sku": sku_partner_id,
                "price": sku_price,
                "stock_quantity": sku_amount,
                "active": bool(safe_get_value(product_data, "isProductActive", True)),
                
                # Dados JSON completos
                "characteristics": characteristics,
                "images": images,
                "skus": skus,
                
                # Status de sincronização
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

def save_orders_to_db_ultra_complete(orders_data, db):
    """
    Salva pedidos no banco de dados com TODOS os campos expandidos
    Função copiada do migrate_orders_ultra_final.py
    """
    for order_data in orders_data:
        try:
            anymarket_id = str(safe_get_value(order_data, "id", ""))
            
            existing_order = db.query(models.Order).filter(
                models.Order.anymarket_id == anymarket_id
            ).first()
            
            # Extrair objetos aninhados
            quote_reconciliation = safe_get_value(order_data, "quoteReconciliation", {})
            invoice = safe_get_value(order_data, "invoice", {})
            shipping = safe_get_value(order_data, "shipping", {})
            billing_address = safe_get_value(order_data, "billingAddress", {})
            anymarket_address = safe_get_value(order_data, "anymarketAddress", {})
            buyer = safe_get_value(order_data, "buyer", {})
            tracking = safe_get_value(order_data, "tracking", {})
            pickup = safe_get_value(order_data, "pickup", {})
            metadata = safe_get_value(order_data, "metadata", {})
            
            # EXTRAIR E EXPANDIR ITEMS_DATA
            items = safe_get_value(order_data, "items", [])
            first_item = items[0] if items else {}
            
            item_product = safe_get_value(first_item, "product", {})
            item_product_id = str(safe_get_value(item_product, "id", ""))
            item_product_title = safe_get_value(item_product, "title", "")
            
            item_sku = safe_get_value(first_item, "sku", {})
            item_sku_id = str(safe_get_value(item_sku, "id", ""))
            item_sku_title = safe_get_value(item_sku, "title", "")
            item_sku_partner_id = safe_get_value(item_sku, "partnerId", "")
            item_sku_ean = safe_get_value(item_sku, "ean", "")
            
            item_amount = float(safe_get_value(first_item, "amount", 0))
            item_unit = float(safe_get_value(first_item, "unit", 0))
            item_gross = float(safe_get_value(first_item, "gross", 0))
            item_total = float(safe_get_value(first_item, "total", 0))
            item_discount = float(safe_get_value(first_item, "discount", 0))
            item_id_in_marketplace = safe_get_value(first_item, "idInMarketPlace", "")
            item_order_item_id = str(safe_get_value(first_item, "orderItemId", ""))
            item_free_shipping = bool(safe_get_value(first_item, "freeShipping", False))
            item_is_catalog = bool(safe_get_value(first_item, "isCatalog", False))
            item_id_in_marketplace_catalog_origin = safe_get_value(first_item, "idInMarketplaceCatalogOrigin", "")
            
            item_shippings = safe_get_value(first_item, "shippings", [])
            first_item_shipping = item_shippings[0] if item_shippings else {}
            item_shipping_id = str(safe_get_value(first_item_shipping, "id", ""))
            item_shipping_type = safe_get_value(first_item_shipping, "shippingtype", "")
            item_shipping_carrier_normalized = safe_get_value(first_item_shipping, "shippingCarrierNormalized", "")
            item_shipping_carrier_type_normalized = safe_get_value(first_item_shipping, "shippingCarrierTypeNormalized", "")
            
            item_stocks = safe_get_value(first_item, "stocks", [])
            first_item_stock = item_stocks[0] if item_stocks else {}
            item_stock_local_id = str(safe_get_value(first_item_stock, "stockLocalId", ""))
            item_stock_amount = float(safe_get_value(first_item_stock, "amount", 0))
            item_stock_name = safe_get_value(first_item_stock, "stockName", "")
            
            total_items = len(items)
            total_items_amount = sum(float(item.get("amount", 0)) for item in items)
            total_items_value = sum(float(item.get("total", 0)) for item in items)
            
            # EXTRAIR E EXPANDIR PAYMENTS_DATA
            payments = safe_get_value(order_data, "payments", [])
            first_payment = payments[0] if payments else {}
            
            payment_method = safe_get_value(first_payment, "method", "")
            payment_status = safe_get_value(first_payment, "status", "")
            payment_value = float(safe_get_value(first_payment, "value", 0))
            payment_marketplace_id = safe_get_value(first_payment, "marketplaceId", "")
            payment_method_normalized = safe_get_value(first_payment, "paymentMethodNormalized", "")
            payment_detail_normalized = safe_get_value(first_payment, "paymentDetailNormalized", "")
            
            total_payments = len(payments)
            total_payments_value = sum(float(payment.get("value", 0)) for payment in payments)
            
            # MAPEAR TODOS OS CAMPOS
            order_fields = {
                "anymarket_id": anymarket_id,
                "account_name": safe_get_value(order_data, "accountName", ""),
                "market_place_id": safe_get_value(order_data, "marketPlaceId", ""),
                "market_place_number": safe_get_value(order_data, "marketPlaceNumber", ""),
                "partner_id": safe_get_value(order_data, "partnerId", ""),
                "marketplace": safe_get_value(order_data, "marketPlace", ""),
                "sub_channel": safe_get_value(order_data, "subChannel", ""),
                "sub_channel_normalized": safe_get_value(order_data, "subChannelNormalized", ""),
                
                "created_at_anymarket": parse_datetime(safe_get_value(order_data, "createdAt")),
                "payment_date": parse_datetime(safe_get_value(order_data, "paymentDate")),
                "cancel_date": parse_datetime(safe_get_value(order_data, "cancelDate")),
                
                "shipping_option_id": safe_get_value(order_data, "shippingOptionId", ""),
                "transmission_status": safe_get_value(order_data, "transmissionStatus", ""),
                "status": safe_get_value(order_data, "status", ""),
                "market_place_status": safe_get_value(order_data, "marketPlaceStatus", ""),
                "market_place_status_complement": safe_get_value(order_data, "marketPlaceStatusComplement", ""),
                "market_place_shipment_status": safe_get_value(order_data, "marketPlaceShipmentStatus", ""),
                
                "document_intermediator": safe_get_value(order_data, "documentIntermediator", ""),
                "intermediate_registration_id": safe_get_value(order_data, "intermediateRegistrationId", ""),
                "document_payment_institution": safe_get_value(order_data, "documentPaymentInstitution", ""),
                "fulfillment": bool(safe_get_value(order_data, "fulfillment", False)),
                
                "quote_id": safe_get_value(quote_reconciliation, "quoteId", ""),
                "quote_price": float(safe_get_value(quote_reconciliation, "price", 0)) if quote_reconciliation.get("price") else None,
                
                "discount": float(safe_get_value(order_data, "discount", 0)),
                "freight": float(safe_get_value(order_data, "freight", 0)),
                "seller_freight": float(safe_get_value(order_data, "sellerFreight", 0)),
                "interest_value": float(safe_get_value(order_data, "interestValue", 0)),
                "gross": float(safe_get_value(order_data, "gross", 0)),
                "total": float(safe_get_value(order_data, "total", 0)),
                
                "market_place_url": safe_get_value(order_data, "marketPlaceUrl", ""),
                
                # Invoice expandido
                "invoice_access_key": safe_get_value(invoice, "accessKey", ""),
                "invoice_series": safe_get_value(invoice, "series", ""),
                "invoice_number": safe_get_value(invoice, "number", ""),
                "invoice_date": parse_datetime(safe_get_value(invoice, "date")),
                "invoice_cfop": safe_get_value(invoice, "cfop", ""),
                "invoice_company_state_tax_id": safe_get_value(invoice, "companyStateTaxId", ""),
                "invoice_link_nfe": safe_get_value(invoice, "linkNfe", ""),
                "invoice_link": safe_get_value(invoice, "invoiceLink", ""),
                "invoice_extra_description": safe_get_value(invoice, "extraDescription", ""),
                
                # Shipping expandido
                "shipping_address": safe_get_value(shipping, "address", ""),
                "shipping_city": safe_get_value(shipping, "city", ""),
                "shipping_comment": safe_get_value(shipping, "comment", ""),
                "shipping_country": safe_get_value(shipping, "country", ""),
                "shipping_country_acronym_normalized": safe_get_value(shipping, "countryAcronymNormalized", ""),
                "shipping_country_name_normalized": safe_get_value(shipping, "countryNameNormalized", ""),
                "shipping_neighborhood": safe_get_value(shipping, "neighborhood", ""),
                "shipping_number": safe_get_value(shipping, "number", ""),
                "shipping_promised_shipping_time": parse_datetime(safe_get_value(shipping, "promisedShippingTime")),
                "shipping_promised_dispatch_time": parse_datetime(safe_get_value(shipping, "promisedDispatchTime")),
                "shipping_receiver_name": safe_get_value(shipping, "receiverName", ""),
                "shipping_reference": safe_get_value(shipping, "reference", ""),
                "shipping_state": safe_get_value(shipping, "state", ""),
                "shipping_state_name_normalized": safe_get_value(shipping, "stateNameNormalized", ""),
                "shipping_street": safe_get_value(shipping, "street", ""),
                "shipping_zip_code": safe_get_value(shipping, "zipCode", ""),
                
                # Billing Address expandido
                "billing_address": safe_get_value(billing_address, "address", ""),
                "billing_city": safe_get_value(billing_address, "city", ""),
                "billing_comment": safe_get_value(billing_address, "comment", ""),
                "billing_country": safe_get_value(billing_address, "country", ""),
                "billing_country_acronym_normalized": safe_get_value(billing_address, "countryAcronymNormalized", ""),
                "billing_country_name_normalized": safe_get_value(billing_address, "countryNameNormalized", ""),
                "billing_neighborhood": safe_get_value(billing_address, "neighborhood", ""),
                "billing_number": safe_get_value(billing_address, "number", ""),
                "billing_reference": safe_get_value(billing_address, "reference", ""),
                "billing_shipment_user_document": safe_get_value(billing_address, "shipmentUserDocument", ""),
                "billing_shipment_user_document_type": safe_get_value(billing_address, "shipmentUserDocumentType", ""),
                "billing_shipment_user_name": safe_get_value(billing_address, "shipmentUserName", ""),
                "billing_state": safe_get_value(billing_address, "state", ""),
                "billing_state_name_normalized": safe_get_value(billing_address, "stateNameNormalized", ""),
                "billing_street": safe_get_value(billing_address, "street", ""),
                "billing_zip_code": safe_get_value(billing_address, "zipCode", ""),
                
                # Anymarket Address expandido
                "anymarket_address": safe_get_value(anymarket_address, "address", ""),
                "anymarket_city": safe_get_value(anymarket_address, "city", ""),
                "anymarket_comment": safe_get_value(anymarket_address, "comment", ""),
                "anymarket_country": safe_get_value(anymarket_address, "country", ""),
                "anymarket_neighborhood": safe_get_value(anymarket_address, "neighborhood", ""),
                "anymarket_number": safe_get_value(anymarket_address, "number", ""),
                "anymarket_promised_shipping_time": parse_datetime(safe_get_value(anymarket_address, "promisedShippingTime")),
                "anymarket_receiver_name": safe_get_value(anymarket_address, "receiverName", ""),
                "anymarket_reference": safe_get_value(anymarket_address, "reference", ""),
                "anymarket_state": safe_get_value(anymarket_address, "state", ""),
                "anymarket_state_acronym_normalized": safe_get_value(anymarket_address, "stateAcronymNormalized", ""),
                "anymarket_street": safe_get_value(anymarket_address, "street", ""),
                "anymarket_zip_code": safe_get_value(anymarket_address, "zipCode", ""),
                
                # Buyer expandido
                "buyer_cell_phone": safe_get_value(buyer, "cellPhone", ""),
                "buyer_document": safe_get_value(buyer, "document", ""),
                "buyer_document_number_normalized": safe_get_value(buyer, "documentNumberNormalized", ""),
                "buyer_document_type": safe_get_value(buyer, "documentType", ""),
                "buyer_email": safe_get_value(buyer, "email", ""),
                "buyer_market_place_id": safe_get_value(buyer, "marketPlaceId", ""),
                "buyer_name": safe_get_value(buyer, "name", ""),
                "buyer_phone": safe_get_value(buyer, "phone", ""),
                "buyer_date_of_birth": parse_datetime(safe_get_value(buyer, "dateOfBirth")),
                "buyer_company_state_tax_id": safe_get_value(buyer, "companyStateTaxId", ""),
                
                # Tracking expandido
                "tracking_carrier": safe_get_value(tracking, "carrier", ""),
                "tracking_date": parse_datetime(safe_get_value(tracking, "date")),
                "tracking_delivered_date": parse_datetime(safe_get_value(tracking, "deliveredDate")),
                "tracking_estimate_date": parse_datetime(safe_get_value(tracking, "estimateDate")),
                "tracking_number": safe_get_value(tracking, "number", ""),
                "tracking_shipped_date": parse_datetime(safe_get_value(tracking, "shippedDate")),
                "tracking_url": safe_get_value(tracking, "url", ""),
                "tracking_carrier_document": safe_get_value(tracking, "carrierDocument", ""),
                "tracking_buffering_date": parse_datetime(safe_get_value(tracking, "bufferingDate")),
                "tracking_delivery_status": safe_get_value(tracking, "deliveryStatus", ""),
                
                # Pickup expandido
                "pickup_id": int(safe_get_value(pickup, "id", 0)) if pickup.get("id") else None,
                "pickup_description": safe_get_value(pickup, "description", ""),
                "pickup_partner_id": int(safe_get_value(pickup, "partnerId", 0)) if pickup.get("partnerId") else None,
                "pickup_marketplace_id": safe_get_value(pickup, "marketplaceId", ""),
                "pickup_receiver_name": safe_get_value(pickup, "receiverName", ""),
                
                "id_account": int(safe_get_value(order_data, "idAccount", 0)) if order_data.get("idAccount") else None,
                
                # Metadados expandidos
                "metadata_number_of_packages": safe_get_value(metadata, "number-of-packages", ""),
                "metadata_cd_zip_code": safe_get_value(metadata, "cdZipCode", ""),
                "metadata_need_invoice_xml": safe_get_value(metadata, "needInvoiceXML", ""),
                "metadata_mshops": safe_get_value(metadata, "mshops", ""),
                "metadata_envvias": safe_get_value(metadata, "Envvias", ""),
                "metadata_via_total_discount_amount": safe_get_value(metadata, "VIAtotalDiscountAmount", ""),
                "metadata_b2w_shipping_type": safe_get_value(metadata, "B2WshippingType", ""),
                "metadata_logistic_type": safe_get_value(metadata, "logistic_type", ""),
                "metadata_print_tag": safe_get_value(metadata, "printTag", ""),
                "metadata_cancel_detail_motivation": safe_get_value(metadata, "canceldetail_motivation", ""),
                "metadata_cancel_detail_code": safe_get_value(metadata, "canceldetail_code", ""),
                "metadata_cancel_detail_description": safe_get_value(metadata, "canceldetail_description", ""),
                "metadata_cancel_detail_requested_by": safe_get_value(metadata, "canceldetail_requested_by", ""),
                "metadata_order_type_name": safe_get_value(metadata, "orderTypeName", ""),
                "metadata_shipping_id": safe_get_value(metadata, "shippingId", ""),
                
                # ITEMS expandidos
                "item_product_id": item_product_id,
                "item_product_title": item_product_title,
                "item_sku_id": item_sku_id,
                "item_sku_title": item_sku_title,
                "item_sku_partner_id": item_sku_partner_id,
                "item_sku_ean": item_sku_ean,
                "item_amount": item_amount,
                "item_unit": item_unit,
                "item_gross": item_gross,
                "item_total": item_total,
                "item_discount": item_discount,
                "item_id_in_marketplace": item_id_in_marketplace,
                "item_order_item_id": item_order_item_id,
                "item_free_shipping": item_free_shipping,
                "item_is_catalog": item_is_catalog,
                "item_id_in_marketplace_catalog_origin": item_id_in_marketplace_catalog_origin,
                "item_shipping_id": item_shipping_id,
                "item_shipping_type": item_shipping_type,
                "item_shipping_carrier_normalized": item_shipping_carrier_normalized,
                "item_shipping_carrier_type_normalized": item_shipping_carrier_type_normalized,
                "item_stock_local_id": item_stock_local_id,
                "item_stock_amount": item_stock_amount,
                "item_stock_name": item_stock_name,
                "total_items": total_items,
                "total_items_amount": total_items_amount,
                "total_items_value": total_items_value,
                
                # PAYMENTS expandidos
                "payment_method": payment_method,
                "payment_status": payment_status,
                "payment_value": payment_value,
                "payment_marketplace_id": payment_marketplace_id,
                "payment_method_normalized": payment_method_normalized,
                "payment_detail_normalized": payment_detail_normalized,
                "total_payments": total_payments,
                "total_payments_value": total_payments_value,
                
                # Dados JSON completos
                "items_data": items,
                "payments_data": payments,
                "shippings_data": safe_get_value(order_data, "shippings", []),
                "stocks_data": safe_get_value(order_data, "stocks", []),
                "metadata_extra": metadata,
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

def update_products_since_date(client, db, since_date):
    """Atualiza produtos criados/modificados desde uma data específica"""
    try:
        logger.info(f"📥 Iniciando atualização de produtos desde: {since_date}")
        
        offset = 0
        limit = 50
        total_updated = 0
        
        # Converter data para string ISO para a API
        since_date_str = since_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        while True:
            logger.info(f"🔍 Buscando produtos: offset {offset}, limit {limit}, since {since_date_str}")
            
            # Buscar produtos da API com filtro de data
            products_response = client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                logger.info("📭 Nenhum produto encontrado.")
                break
            
            # Filtrar produtos por data de criação (se a API não suportar filtro nativo)
            filtered_products = []
            for product in products:
                product_created_at = parse_datetime(product.get("createdAt"))
                if product_created_at and product_created_at >= since_date:
                    filtered_products.append(product)
            
            if not filtered_products:
                logger.info(f"📅 Nenhum produto novo desde {since_date_str}")
                break
            
            logger.info(f"📦 Processando {len(filtered_products)} produtos novos/atualizados...")
            
            # Salvar no banco
            save_products_to_db_ultra_complete(filtered_products, db)
            
            total_updated += len(filtered_products)
            offset += limit
            
            logger.info(f"✅ Total atualizado até agora: {total_updated}")
            
            # Se retornou menos que o limite ou não há produtos filtrados, parar
            if len(products) < limit or len(filtered_products) == 0:
                break
            
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
        
        logger.info(f"🎉 Atualização de produtos concluída! Total: {total_updated}")
        return total_updated
        
    except Exception as e:
        logger.error(f"❌ Erro na atualização de produtos: {e}")
        return 0

def update_orders_since_date(client, db, since_date):
    """Atualiza pedidos criados/modificados desde uma data específica"""
    try:
        logger.info(f"📥 Iniciando atualização de pedidos desde: {since_date}")
        
        offset = 0
        limit = 50
        total_updated = 0
        
        # Converter data para string ISO para a API
        since_date_str = since_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        
        while True:
            logger.info(f"🔍 Buscando pedidos: offset {offset}, limit {limit}, since {since_date_str}")
            
            # Buscar pedidos da API
            orders_response = client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                logger.info("📭 Nenhum pedido encontrado.")
                break
            
            # Filtrar pedidos por data de criação
            filtered_orders = []
            for order in orders:
                order_created_at = parse_datetime(order.get("createdAt"))
                if order_created_at and order_created_at >= since_date:
                    filtered_orders.append(order)
            
            if not filtered_orders:
                logger.info(f"📅 Nenhum pedido novo desde {since_date_str}")
                break
            
            logger.info(f"📦 Processando {len(filtered_orders)} pedidos novos/atualizados...")
            
            # Salvar no banco
            save_orders_to_db_ultra_complete(filtered_orders, db)
            
            total_updated += len(filtered_orders)
            offset += limit
            
            logger.info(f"✅ Total atualizado até agora: {total_updated}")
            
            # Se retornou menos que o limite ou não há pedidos filtrados, parar
            if len(orders) < limit or len(filtered_orders) == 0:
                break
            
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
        
        logger.info(f"🎉 Atualização de pedidos concluída! Total: {total_updated}")
        return total_updated
        
    except Exception as e:
        logger.error(f"❌ Erro na atualização de pedidos: {e}")
        return 0

def create_daily_summary(products_updated, orders_updated, start_time, end_time):
    """Cria um resumo da sincronização diária"""
    try:
        duration = end_time - start_time
        
        summary = {
            "date": datetime.now().isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration),
            "products_updated": products_updated,
            "orders_updated": orders_updated,
            "total_records": products_updated + orders_updated,
            "status": "success" if (products_updated >= 0 and orders_updated >= 0) else "error"
        }
        
        # Salvar resumo em arquivo JSON
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
        
        # Produtos recentes (últimas 24h)
        yesterday = datetime.now() - timedelta(days=1)
        recent_products = db.query(models.Product).filter(
            models.Product.created_at >= yesterday
        ).count()
        
        recent_orders = db.query(models.Order).filter(
            models.Order.created_at >= yesterday
        ).count()
        
        # Produtos e pedidos com problemas de sincronização
        products_with_errors = db.query(models.Product).filter(
            models.Product.sync_status == "error"
        ).count()
        
        logger.info(f"📊 Status do banco de dados:")
        logger.info(f"   - Total produtos: {total_products}")
        logger.info(f"   - Total pedidos: {total_orders}")
        logger.info(f"   - Produtos recentes (24h): {recent_products}")
        logger.info(f"   - Pedidos recentes (24h): {recent_orders}")
        logger.info(f"   - Produtos com erro: {products_with_errors}")
        
        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "recent_products": recent_products,
            "recent_orders": recent_orders,
            "products_with_errors": products_with_errors
        }
        
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {e}")
        return None

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
    print("3. Importar apenas dados novos desde essas datas")
    print("4. Atualizar registros existentes se necessário")
    print("5. Gerar relatório de sincronização")
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
        
        # Passo 3: Verificar status final
        print("\n" + "="*40)
        logger.info("📊 Verificando status final...")
        final_status = verify_sync_status(db)
        
        # Calcular estatísticas
        end_time = datetime.now()
        
        # Passo 4: Criar resumo
        print("\n" + "="*40)
        summary_file = create_daily_summary(products_updated, orders_updated, start_time, end_time)
        
        # Resultado final
        print("\n" + "🎉 ATUALIZAÇÃO DIÁRIA CONCLUÍDA! " + "🎉")
        print("=" * 60)
        print(f"⏰ Iniciada: {start_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"⏰ Finalizada: {end_time.strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"⏱️  Duração: {end_time - start_time}")
        print(f"🛍️  Produtos atualizados: {products_updated}")
        print(f"📦 Pedidos atualizados: {orders_updated}")
        print(f"📊 Total de registros: {products_updated + orders_updated}")
        
        if summary_file:
            print(f"📄 Relatório salvo: {summary_file}")
        
        print("")
        print("💡 Estatísticas do banco:")
        if final_status:
            print(f"   - Total produtos: {final_status['total_products']}")
            print(f"   - Total pedidos: {final_status['total_orders']}")
            print(f"   - Produtos recentes: {final_status['recent_products']}")
            print(f"   - Pedidos recentes: {final_status['recent_orders']}")
        
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