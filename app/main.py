from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
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

app = FastAPI(
    title="Anymarket Backend - API Completa", 
    version="3.0.0",
    description="API completa com todos os campos expandidos de Products e Orders"
)

# Instanciar cliente da API
anymarket_client = AnymarketClient()

# Incluir todas as funções auxiliares
def safe_get_value(data: dict, key: str, default=None):
    """Função auxiliar para extrair valores de forma segura"""
    value = data.get(key, default)
    return value if value is not None else default

def parse_datetime(date_string: Optional[str]) -> Optional[datetime]:
    """Converte string de data ISO para datetime"""
    if not date_string:
        return None
    try:
        if date_string.endswith('Z'):
            date_string = date_string[:-1] + '+00:00'
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        return None

# FUNÇÃO ULTRA COMPLETA - Esta é a versão correta para usar
def save_orders_to_db_ultra_complete(orders_data: List[Dict], db: Session):
    """
    Salva pedidos no banco de dados com TODOS os campos expandidos
    Incluindo items_data e payments_data expandidos em colunas individuais
    """
    for order_data in orders_data:
        try:
            anymarket_id = str(safe_get_value(order_data, "id", ""))
            
            # Verifica se pedido já existe
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
            
            # ===================================================================
            # EXTRAIR E EXPANDIR ITEMS_DATA
            # ===================================================================
            items = safe_get_value(order_data, "items", [])
            
            # Campos do primeiro item (ou valores padrão se não houver items)
            first_item = items[0] if items else {}
            
            # Item Product
            item_product = safe_get_value(first_item, "product", {})
            item_product_id = str(safe_get_value(item_product, "id", ""))
            item_product_title = safe_get_value(item_product, "title", "")
            
            # Item SKU
            item_sku = safe_get_value(first_item, "sku", {})
            item_sku_id = str(safe_get_value(item_sku, "id", ""))
            item_sku_title = safe_get_value(item_sku, "title", "")
            item_sku_partner_id = safe_get_value(item_sku, "partnerId", "")
            item_sku_ean = safe_get_value(item_sku, "ean", "")
            
            # Item valores
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
            
            # Item Shippings (primeiro shipping do primeiro item)
            item_shippings = safe_get_value(first_item, "shippings", [])
            first_item_shipping = item_shippings[0] if item_shippings else {}
            item_shipping_id = str(safe_get_value(first_item_shipping, "id", ""))
            item_shipping_type = safe_get_value(first_item_shipping, "shippingtype", "")
            item_shipping_carrier_normalized = safe_get_value(first_item_shipping, "shippingCarrierNormalized", "")
            item_shipping_carrier_type_normalized = safe_get_value(first_item_shipping, "shippingCarrierTypeNormalized", "")
            
            # Item Stocks (primeiro stock do primeiro item)
            item_stocks = safe_get_value(first_item, "stocks", [])
            first_item_stock = item_stocks[0] if item_stocks else {}
            item_stock_local_id = str(safe_get_value(first_item_stock, "stockLocalId", ""))
            item_stock_amount = float(safe_get_value(first_item_stock, "amount", 0))
            item_stock_name = safe_get_value(first_item_stock, "stockName", "")
            
            # Campos derivados dos items
            total_items = len(items)
            total_items_amount = sum(float(item.get("amount", 0)) for item in items)
            total_items_value = sum(float(item.get("total", 0)) for item in items)
            
            # ===================================================================
            # EXTRAIR E EXPANDIR PAYMENTS_DATA
            # ===================================================================
            payments = safe_get_value(order_data, "payments", [])
            
            # Campos do primeiro payment (ou valores padrão se não houver payments)
            first_payment = payments[0] if payments else {}
            
            payment_method = safe_get_value(first_payment, "method", "")
            payment_status = safe_get_value(first_payment, "status", "")
            payment_value = float(safe_get_value(first_payment, "value", 0))
            payment_marketplace_id = safe_get_value(first_payment, "marketplaceId", "")
            payment_method_normalized = safe_get_value(first_payment, "paymentMethodNormalized", "")
            payment_detail_normalized = safe_get_value(first_payment, "paymentDetailNormalized", "")
            
            # Campos derivados dos payments
            total_payments = len(payments)
            total_payments_value = sum(float(payment.get("value", 0)) for payment in payments)
            
            # ===================================================================
            # MAPEAR TODOS OS CAMPOS PARA O OBJETO ORDER
            # ===================================================================
            order_fields = {
                # Campos básicos
                "anymarket_id": anymarket_id,
                "account_name": safe_get_value(order_data, "accountName", ""),
                "market_place_id": safe_get_value(order_data, "marketPlaceId", ""),
                "market_place_number": safe_get_value(order_data, "marketPlaceNumber", ""),
                "partner_id": safe_get_value(order_data, "partnerId", ""),
                "marketplace": safe_get_value(order_data, "marketPlace", ""),
                "sub_channel": safe_get_value(order_data, "subChannel", ""),
                "sub_channel_normalized": safe_get_value(order_data, "subChannelNormalized", ""),
                
                # Datas importantes
                "created_at_anymarket": parse_datetime(safe_get_value(order_data, "createdAt")),
                "payment_date": parse_datetime(safe_get_value(order_data, "paymentDate")),
                "cancel_date": parse_datetime(safe_get_value(order_data, "cancelDate")),
                
                # Status e informações do pedido
                "shipping_option_id": safe_get_value(order_data, "shippingOptionId", ""),
                "transmission_status": safe_get_value(order_data, "transmissionStatus", ""),
                "status": safe_get_value(order_data, "status", ""),
                "market_place_status": safe_get_value(order_data, "marketPlaceStatus", ""),
                "market_place_status_complement": safe_get_value(order_data, "marketPlaceStatusComplement", ""),
                "market_place_shipment_status": safe_get_value(order_data, "marketPlaceShipmentStatus", ""),
                
                # Documentos e intermediários
                "document_intermediator": safe_get_value(order_data, "documentIntermediator", ""),
                "intermediate_registration_id": safe_get_value(order_data, "intermediateRegistrationId", ""),
                "document_payment_institution": safe_get_value(order_data, "documentPaymentInstitution", ""),
                "fulfillment": bool(safe_get_value(order_data, "fulfillment", False)),
                
                # Cotação (quoteReconciliation object)
                "quote_id": safe_get_value(quote_reconciliation, "quoteId", ""),
                "quote_price": float(safe_get_value(quote_reconciliation, "price", 0)) if quote_reconciliation.get("price") else None,
                
                # Valores financeiros
                "discount": float(safe_get_value(order_data, "discount", 0)),
                "freight": float(safe_get_value(order_data, "freight", 0)),
                "seller_freight": float(safe_get_value(order_data, "sellerFreight", 0)),
                "interest_value": float(safe_get_value(order_data, "interestValue", 0)),
                "gross": float(safe_get_value(order_data, "gross", 0)),
                "total": float(safe_get_value(order_data, "total", 0)),
                
                # URLs
                "market_place_url": safe_get_value(order_data, "marketPlaceUrl", ""),
                
                # Invoice (nota fiscal object) - TODOS os campos
                "invoice_access_key": safe_get_value(invoice, "accessKey", ""),
                "invoice_series": safe_get_value(invoice, "series", ""),
                "invoice_number": safe_get_value(invoice, "number", ""),
                "invoice_date": parse_datetime(safe_get_value(invoice, "date")),
                "invoice_cfop": safe_get_value(invoice, "cfop", ""),
                "invoice_company_state_tax_id": safe_get_value(invoice, "companyStateTaxId", ""),
                "invoice_link_nfe": safe_get_value(invoice, "linkNfe", ""),
                "invoice_link": safe_get_value(invoice, "invoiceLink", ""),
                "invoice_extra_description": safe_get_value(invoice, "extraDescription", ""),
                
                # Shipping (endereço de entrega object) - TODOS os campos
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
                
                # Billing Address (endereço de cobrança object) - TODOS os campos
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
                
                # Anymarket Address (object) - TODOS os campos
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
                
                # Buyer (comprador object) - TODOS os campos
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
                
                # Tracking (rastreamento object) - TODOS os campos
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
                
                # Pickup (retirada object) - TODOS os campos
                "pickup_id": int(safe_get_value(pickup, "id", 0)) if pickup.get("id") else None,
                "pickup_description": safe_get_value(pickup, "description", ""),
                "pickup_partner_id": int(safe_get_value(pickup, "partnerId", 0)) if pickup.get("partnerId") else None,
                "pickup_marketplace_id": safe_get_value(pickup, "marketplaceId", ""),
                "pickup_receiver_name": safe_get_value(pickup, "receiverName", ""),
                
                # ID Account
                "id_account": int(safe_get_value(order_data, "idAccount", 0)) if order_data.get("idAccount") else None,
                
                # Metadados (metadata object) - TODOS os campos principais
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
                
                # ===================================================================
                # ITEMS EXPANDIDOS (NOVOS CAMPOS)
                # ===================================================================
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
                
                # ===================================================================
                # PAYMENTS EXPANDIDOS (NOVOS CAMPOS)
                # ===================================================================
                "payment_method": payment_method,
                "payment_status": payment_status,
                "payment_value": payment_value,
                "payment_marketplace_id": payment_marketplace_id,
                "payment_method_normalized": payment_method_normalized,
                "payment_detail_normalized": payment_detail_normalized,
                "total_payments": total_payments,
                "total_payments_value": total_payments_value,
                
                # ===================================================================
                # DADOS JSON COMPLETOS (para referência completa)
                # ===================================================================
                "payments_data": payments,
                "items_data": items,
                "shippings_data": safe_get_value(order_data, "shippings", []),
                "stocks_data": safe_get_value(order_data, "stocks", []),
                "metadata_extra": metadata,
            }
            
            if existing_order:
                # Atualizar pedido existente
                for field, value in order_fields.items():
                    if field != "anymarket_id":
                        setattr(existing_order, field, value)
                existing_order.updated_at = datetime.now()
                logger.info(f"📦 Order atualizado: {anymarket_id} - Items: {total_items}, Payments: {total_payments}")
            else:
                # Criar novo pedido
                new_order = models.Order(**order_fields)
                db.add(new_order)
                logger.info(f"✨ Order criado: {anymarket_id} - Items: {total_items}, Payments: {total_payments}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar order {order_data.get('id')}: {e}")
            continue
    
    db.commit()

# Função completa de salvamento de products
def save_products_to_db_complete(products_data: List[Dict], db: Session):
    """
    Salva produtos no banco de dados com TODOS os campos expandidos
    Cada objeto aninhado vira colunas individuais
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
            characteristics = safe_get_value(product_data, "characteristics", [])
            images = safe_get_value(product_data, "images", [])
            skus = safe_get_value(product_data, "skus", [])
            
            # Calcular campos derivados dos SKUs
            total_skus = len(skus)
            min_price = None
            max_price = None
            total_stock = 0
            main_sku = None
            main_price = None
            
            if skus:
                prices = [float(sku.get("price", 0)) for sku in skus if sku.get("price")]
                amounts = [int(sku.get("amount", 0)) for sku in skus if sku.get("amount")]
                
                if prices:
                    min_price = min(prices)
                    max_price = max(prices)
                    main_price = prices[0]  # Preço do primeiro SKU
                
                if amounts:
                    total_stock = sum(amounts)
                
                # SKU principal (primeiro SKU)
                main_sku = skus[0].get("partnerId", "") if skus else ""
            
            # Calcular campos derivados das imagens
            total_images = len(images)
            main_image_url = ""
            
            if images:
                # Procurar imagem principal
                for image in images:
                    if image.get("main", False):
                        main_image_url = image.get("url", "")
                        break
                
                # Se não encontrou imagem principal, usar a primeira
                if not main_image_url and images:
                    main_image_url = images[0].get("url", "")
            
            # Mapear TODOS os campos para colunas individuais
            product_fields = {
                # Campos básicos
                "anymarket_id": anymarket_id,
                "title": safe_get_value(product_data, "title", ""),
                "description": safe_get_value(product_data, "description", ""),
                "external_id_product": safe_get_value(product_data, "externalIdProduct", ""),
                
                # Category expandida (objeto category → colunas individuais)
                "category_id": str(safe_get_value(category, "id", "")),
                "category_name": safe_get_value(category, "name", ""),
                "category_path": safe_get_value(category, "path", ""),
                
                # Brand expandida (objeto brand → colunas individuais)
                "brand_id": str(safe_get_value(brand, "id", "")),
                "brand_name": safe_get_value(brand, "name", ""),
                "brand_reduced_name": safe_get_value(brand, "reducedName", ""),
                "brand_partner_id": safe_get_value(brand, "partnerId", ""),
                
                # NBM expandido (objeto nbm → colunas individuais)
                "nbm_id": safe_get_value(nbm, "id", ""),
                "nbm_description": safe_get_value(nbm, "description", ""),
                
                # Origin expandido (objeto origin → colunas individuais)
                "origin_id": str(safe_get_value(origin, "id", "")),
                "origin_description": safe_get_value(origin, "description", ""),
                
                # Informações básicas do produto
                "model": safe_get_value(product_data, "model", ""),
                "video_url": safe_get_value(product_data, "videoUrl", ""),
                "gender": safe_get_value(product_data, "gender", ""),
                
                # Garantia
                "warranty_time": int(safe_get_value(product_data, "warrantyTime", 0)) if product_data.get("warrantyTime") else None,
                "warranty_text": safe_get_value(product_data, "warrantyText", ""),
                
                # Dimensões e peso
                "height": float(safe_get_value(product_data, "height", 0)) if product_data.get("height") else None,
                "width": float(safe_get_value(product_data, "width", 0)) if product_data.get("width") else None,
                "weight": float(safe_get_value(product_data, "weight", 0)) if product_data.get("weight") else None,
                "length": float(safe_get_value(product_data, "length", 0)) if product_data.get("length") else None,
                
                # Preços e configurações
                "price_factor": float(safe_get_value(product_data, "priceFactor", 0)) if product_data.get("priceFactor") else None,
                "calculated_price": bool(safe_get_value(product_data, "calculatedPrice", False)),
                "definition_price_scope": safe_get_value(product_data, "definitionPriceScope", ""),
                
                # Status e configurações do produto
                "has_variations": bool(safe_get_value(product_data, "hasVariations", False)),
                "is_product_active": bool(safe_get_value(product_data, "isProductActive", True)),
                "product_type": safe_get_value(product_data, "type", ""),
                "allow_automatic_sku_marketplace_creation": bool(safe_get_value(product_data, "allowAutomaticSkuMarketplaceCreation", True)),
                
                # Dados JSON para arrays complexos
                "characteristics": characteristics,
                "images": images,
                "skus": skus,
                
                # Campos derivados para facilitar consultas
                "sku": main_sku,
                "price": main_price,
                "stock_quantity": total_stock,
                "active": bool(safe_get_value(product_data, "isProductActive", True)),
                "main_image_url": main_image_url,
                "total_images": total_images,
                "total_skus": total_skus,
                "min_price": min_price,
                "max_price": max_price,
                "total_stock": total_stock,
                
                # Status de sincronização
                "sync_status": "synced",
                "last_sync_date": datetime.now(),
            }
            
            if existing_product:
                # Atualizar produto existente
                for field, value in product_fields.items():
                    if field != "anymarket_id":  # Não atualizar o ID
                        setattr(existing_product, field, value)
                existing_product.updated_at = datetime.now()
                logger.info(f"📦 Produto atualizado: {anymarket_id} - {product_fields['title'][:50]}...")
            else:
                # Criar novo produto
                new_product = models.Product(**product_fields)
                db.add(new_product)
                logger.info(f"✨ Produto criado: {anymarket_id} - {product_fields['title'][:50]}...")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar produto {product_data.get('id')}: {e}")
            continue
    
    db.commit()

@app.get("/")
def read_root():
    return {
        "message": "Anymarket Backend API - Versão Ultra Completa",
        "version": "3.0.0",
        "features": [
            "Produtos com campos expandidos",
            "Orders com campos ultra expandidos (items + payments)",
            "Objetos aninhados em colunas individuais",
            "Endpoints especializados para consultas avançadas"
        ]
    }

# =============================================================================
# ENDPOINTS DE SINCRONIZAÇÃO - USANDO A FUNÇÃO ULTRA COMPLETA
# =============================================================================

@app.post("/sync/products")
def sync_products(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos da API Anymarket com TODOS os campos expandidos"""
    def sync_task():
        offset = 0
        limit = 50
        total_products = 0
        
        logger.info("🚀 Iniciando sincronização COMPLETA de produtos...")
        
        while True:
            logger.info(f"🔍 Buscando produtos: offset {offset}, limit {limit}")
            products_response = anymarket_client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                break
            
            save_products_to_db_complete(products, db)
            total_products += len(products)
            offset += limit
            
            logger.info(f"📊 Total de produtos processados: {total_products}")
            
            if len(products) < limit:
                break
        
        logger.info(f"🎉 Sincronização de produtos concluída. Total: {total_products}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização COMPLETA de produtos iniciada"}

@app.post("/sync/orders")
def sync_orders(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza orders da API Anymarket com TODOS os campos ULTRA expandidos (items + payments)"""
    def sync_task():
        offset = 0
        limit = 50
        total_orders = 0
        
        logger.info("🚀 Iniciando sincronização ULTRA COMPLETA de orders...")
        
        while True:
            logger.info(f"🔍 Buscando orders: offset {offset}, limit {limit}")
            orders_response = anymarket_client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                break
            
            # USAR A FUNÇÃO ULTRA COMPLETA
            save_orders_to_db_ultra_complete(orders, db)
            total_orders += len(orders)
            offset += limit
            
            logger.info(f"📊 Total de orders processados: {total_orders}")
            
            if len(orders) < limit:
                break
        
        logger.info(f"🎉 Sincronização ULTRA COMPLETA de orders concluída. Total: {total_orders}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização ULTRA COMPLETA de orders iniciada (com items e payments expandidos)"}

@app.post("/sync/all")
def sync_all(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos E orders com versão ULTRA COMPLETA"""
    def sync_all_task():
        logger.info("🚀 Iniciando sincronização ULTRA COMPLETA (produtos + orders)...")
        
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
            
            save_products_to_db_complete(products, db)
            total_products += len(products)
            offset += limit
            
            if len(products) < limit:
                break
        
        logger.info(f"✅ Produtos sincronizados: {total_products}")
        
        # Sincronizar orders com versão ULTRA COMPLETA
        offset = 0
        total_orders = 0
        
        logger.info("📋 Fase 2: Sincronizando orders (ULTRA COMPLETA)...")
        while True:
            orders_response = anymarket_client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                break
            
            # USAR A FUNÇÃO ULTRA COMPLETA
            save_orders_to_db_ultra_complete(orders, db)
            total_orders += len(orders)
            offset += limit
            
            if len(orders) < limit:
                break
        
        logger.info(f"✅ Orders sincronizados: {total_orders}")
        logger.info(f"🎉 Sincronização ULTRA COMPLETA finalizada! Produtos: {total_products}, Orders: {total_orders}")
    
    background_tasks.add_task(sync_all_task)
    return {"message": "Sincronização ULTRA COMPLETA iniciada (produtos + orders com items e payments expandidos)"}

# =============================================================================
# ENDPOINTS DE PRODUCTS - BÁSICOS E EXPANDIDOS
# =============================================================================

@app.get("/products", response_model=List[schemas.ProductSummary])
def get_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista produtos do banco de dados (resumo)"""
    products = db.query(models.Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/full", response_model=List[schemas.Product])
def get_products_full(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista produtos do banco de dados (todos os campos expandidos)"""
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

# =============================================================================
# ENDPOINTS DE ORDERS - BÁSICOS E ULTRA EXPANDIDOS
# =============================================================================

@app.get("/orders", response_model=List[schemas.OrderSummary])
def get_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista orders do banco de dados (resumo)"""
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/full", response_model=List[schemas.Order])
def get_orders_full(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista orders do banco de dados (todos os campos ULTRA expandidos)"""
    orders = db.query(models.Order).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/{order_id}", response_model=schemas.Order)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Busca um order específico por ID"""
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order não encontrado")
    return order

# =============================================================================
# ENDPOINTS ESPECIALIZADOS PARA ITEMS E PAYMENTS EXPANDIDOS
# =============================================================================

@app.get("/orders/product/{product_id}")
def get_orders_by_product(product_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders que contêm um produto específico (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.item_product_id == product_id
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/sku/{sku_partner_id}")
def get_orders_by_sku(sku_partner_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders que contêm um SKU específico (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.item_sku_partner_id == sku_partner_id
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/payment-method/{payment_method}")
def get_orders_by_payment_method(payment_method: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders com método de pagamento específico (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.payment_method_normalized.ilike(f"%{payment_method}%")
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/free-shipping")
def get_orders_with_free_shipping(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders com frete grátis (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.item_free_shipping == True
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/stock/{stock_name}")
def get_orders_by_stock_location(stock_name: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders de um local de estoque específico (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.item_stock_name.ilike(f"%{stock_name}%")
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/item-value-range")
def get_orders_by_item_value_range(
    min_value: float = Query(..., description="Valor mínimo do item"),
    max_value: float = Query(..., description="Valor máximo do item"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Retorna orders com valor de item em uma faixa específica (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.item_total.between(min_value, max_value)
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/catalog-products")
def get_orders_with_catalog_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders que contêm produtos do catálogo (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.item_is_catalog == True
    ).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/payment-status/{payment_status}")
def get_orders_by_payment_status(payment_status: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna orders com status de pagamento específico (campo expandido)"""
    orders = db.query(models.Order).filter(
        models.Order.payment_status == payment_status
    ).offset(skip).limit(limit).all()
    return orders

# =============================================================================
# ENDPOINTS DE ESTATÍSTICAS ULTRA DETALHADAS
# =============================================================================

@app.get("/stats/orders/ultra-detailed")
def get_orders_statistics_ultra_detailed(db: Session = Depends(get_db)):
    """Estatísticas ultra detalhadas incluindo items e payments expandidos"""
    from sqlalchemy import func
    
    # Estatísticas básicas
    total_orders = db.query(models.Order).count()
    orders_with_items = db.query(models.Order).filter(models.Order.total_items > 0).count()
    orders_with_payments = db.query(models.Order).filter(models.Order.total_payments > 0).count()
    
    # Estatísticas de items
    total_items_sold = db.query(func.sum(models.Order.total_items_amount)).scalar() or 0
    total_items_value = db.query(func.sum(models.Order.total_items_value)).scalar() or 0
    avg_items_per_order = db.query(func.avg(models.Order.total_items)).scalar() or 0
    
    # Estatísticas de payments
    total_payments_value = db.query(func.sum(models.Order.total_payments_value)).scalar() or 0
    avg_payments_per_order = db.query(func.avg(models.Order.total_payments)).scalar() or 0
    
    # Top produtos vendidos
    top_products = db.query(
        models.Order.item_product_title,
        func.count(models.Order.id).label('orders_count'),
        func.sum(models.Order.item_amount).label('total_quantity')
    ).filter(
        models.Order.item_product_title.isnot(None),
        models.Order.item_product_title != ""
    ).group_by(
        models.Order.item_product_title
    ).order_by(func.count(models.Order.id).desc()).limit(10).all()
    
    # Top SKUs vendidos
    top_skus = db.query(
        models.Order.item_sku_partner_id,
        models.Order.item_sku_title,
        func.count(models.Order.id).label('orders_count'),
        func.sum(models.Order.item_amount).label('total_quantity')
    ).filter(
        models.Order.item_sku_partner_id.isnot(None),
        models.Order.item_sku_partner_id != ""
    ).group_by(
        models.Order.item_sku_partner_id, models.Order.item_sku_title
    ).order_by(func.count(models.Order.id).desc()).limit(10).all()
    
    # Top métodos de pagamento
    top_payment_methods = db.query(
        models.Order.payment_method_normalized,
        func.count(models.Order.id).label('count'),
        func.sum(models.Order.payment_value).label('total_value')
    ).filter(
        models.Order.payment_method_normalized.isnot(None),
        models.Order.payment_method_normalized != ""
    ).group_by(
        models.Order.payment_method_normalized
    ).order_by(func.count(models.Order.id).desc()).all()
    
    # Estatísticas de frete
    free_shipping_orders = db.query(models.Order).filter(models.Order.item_free_shipping == True).count()
    catalog_orders = db.query(models.Order).filter(models.Order.item_is_catalog == True).count()
    
    # Top locais de estoque
    top_stock_locations = db.query(
        models.Order.item_stock_name,
        func.count(models.Order.id).label('orders_count')
    ).filter(
        models.Order.item_stock_name.isnot(None),
        models.Order.item_stock_name != ""
    ).group_by(
        models.Order.item_stock_name
    ).order_by(func.count(models.Order.id).desc()).limit(5).all()
    
    return {
        "orders": {
            "total_orders": total_orders,
            "orders_with_items": orders_with_items,
            "orders_with_payments": orders_with_payments,
            "free_shipping_orders": free_shipping_orders,
            "catalog_orders": catalog_orders
        },
        "items": {
            "total_items_sold": float(total_items_sold),
            "total_items_value": float(total_items_value),
            "avg_items_per_order": float(avg_items_per_order)
        },
        "payments": {
            "total_payments_value": float(total_payments_value),
            "avg_payments_per_order": float(avg_payments_per_order)
        },
        "top_products": [
            {
                "product_title": stat.item_product_title,
                "orders_count": stat.orders_count,
                "total_quantity": float(stat.total_quantity)
            }
            for stat in top_products
        ],
        "top_skus": [
            {
                "sku_partner_id": stat.item_sku_partner_id,
                "sku_title": stat.item_sku_title,
                "orders_count": stat.orders_count,
                "total_quantity": float(stat.total_quantity)
            }
            for stat in top_skus
        ],
        "top_payment_methods": [
            {
                "method": stat.payment_method_normalized,
                "orders_count": stat.count,
                "total_value": float(stat.total_value) if stat.total_value else 0
            }
            for stat in top_payment_methods
        ],
        "top_stock_locations": [
            {
                "stock_name": stat.item_stock_name,
                "orders_count": stat.orders_count
            }
            for stat in top_stock_locations
        ]
    }

# =============================================================================
# ENDPOINTS DE EXEMPLO E DEMONSTRAÇÃO ULTRA COMPLETA
# =============================================================================

@app.get("/examples/order-ultra-complete")
def get_order_ultra_complete_example(db: Session = Depends(get_db)):
    """Exemplo de order com TODOS os campos ULTRA expandidos"""
    order = db.query(models.Order).first()
    
    if not order:
        return {"message": "Nenhum order encontrado. Execute a sincronização primeiro."}
    
    return {
        "basic_fields": {
            "id": order.id,
            "anymarket_id": order.anymarket_id,
            "marketplace": order.marketplace,
            "status": order.status,
            "total": order.total
        },
        "buyer_expanded": {
            "buyer_name": order.buyer_name,
            "buyer_email": order.buyer_email,
            "buyer_phone": order.buyer_phone,
            "buyer_document": order.buyer_document,
            "buyer_document_type": order.buyer_document_type
        },
        "shipping_expanded": {
            "shipping_street": order.shipping_street,
            "shipping_number": order.shipping_number,
            "shipping_city": order.shipping_city,
            "shipping_state": order.shipping_state,
            "shipping_zip_code": order.shipping_zip_code,
            "shipping_receiver_name": order.shipping_receiver_name
        },
        "items_expanded_NEW": {
            "item_product_id": order.item_product_id,
            "item_product_title": order.item_product_title,
            "item_sku_id": order.item_sku_id,
            "item_sku_title": order.item_sku_title,
            "item_sku_partner_id": order.item_sku_partner_id,
            "item_sku_ean": order.item_sku_ean,
            "item_amount": order.item_amount,
            "item_unit": order.item_unit,
            "item_total": order.item_total,
            "item_free_shipping": order.item_free_shipping,
            "item_is_catalog": order.item_is_catalog,
            "item_stock_name": order.item_stock_name,
            "total_items": order.total_items,
            "total_items_amount": order.total_items_amount,
            "total_items_value": order.total_items_value
        },
        "payments_expanded_NEW": {
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "payment_value": order.payment_value,
            "payment_method_normalized": order.payment_method_normalized,
            "payment_detail_normalized": order.payment_detail_normalized,
            "total_payments": order.total_payments,
            "total_payments_value": order.total_payments_value
        },
        "json_data_complete": {
            "items_data": order.items_data,
            "payments_data": order.payments_data,
            "shippings_data": order.shippings_data,
            "metadata_extra": order.metadata_extra
        }
    }

@app.get("/examples/structure-ultra-comparison")
def get_structure_ultra_comparison():
    """Comparação entre estrutura básica vs ultra expandida"""
    return {
        "antes_basic_structure": {
            "orders": {
                "campos": ["id", "anymarket_id", "marketplace", "status", "total_amount", "customer_name"],
                "total": 6,
                "items": "JSON completo apenas",
                "payments": "JSON completo apenas"
            }
        },
        "depois_ultra_expanded_structure": {
            "orders": {
                "campos_basicos": 15,
                "buyer_expandido": 10,
                "shipping_expandido": 15,
                "billing_expandido": 13,
                "invoice_expandido": 9,
                "tracking_expandido": 10,
                "metadata_expandido": 15,
                "items_expandido_NOVO": 18,
                "payments_expandido_NOVO": 7,
                "total": 112,
                "items": "Expandido em colunas individuais + JSON completo",
                "payments": "Expandido em colunas individuais + JSON completo"
            }
        },
        "novos_campos_items": [
            "item_product_id", "item_product_title",
            "item_sku_id", "item_sku_title", "item_sku_partner_id", "item_sku_ean",
            "item_amount", "item_unit", "item_total", "item_discount",
            "item_free_shipping", "item_is_catalog",
            "item_stock_name", "item_stock_amount",
            "total_items", "total_items_amount", "total_items_value"
        ],
        "novos_campos_payments": [
            "payment_method", "payment_status", "payment_value",
            "payment_method_normalized", "payment_detail_normalized",
            "total_payments", "total_payments_value"
        ],
        "beneficios_ultra": [
            "Consultas SQL diretas em items e payments",
            "Filtros por produto/SKU específico",
            "Análises de métodos de pagamento",
            "Relatórios de frete grátis",
            "Estatísticas por local de estoque",
            "Performance otimizada para BI",
            "Dados normalizados + JSON completo"
        ]
    }

# =============================================================================
# HEALTH CHECK E VALIDAÇÃO
# =============================================================================

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check da aplicação"""
    try:
        # Testar conexão com banco
        products_count = db.query(models.Product).count()
        orders_count = db.query(models.Order).count()
        
        # Testar conexão com API Anymarket
        try:
            test_response = anymarket_client.get_products(limit=1, offset=0)
            api_status = "ok" if test_response.get("content") is not None else "error"
        except:
            api_status = "error"
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "ok",
                "products_count": products_count,
                "orders_count": orders_count
            },
            "anymarket_api": {
                "status": api_status
            },
            "version": "3.0.0 - ULTRA COMPLETA",
            "features": [
                "Orders com items e payments expandidos",
                "112 campos expandidos por order",
                "Consultas SQL diretas em todos os campos"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)