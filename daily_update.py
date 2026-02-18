#!/usr/bin/env python3
"""
Script de atualização diária - Anymarket Backend
Sincroniza products, orders, sku_marketplaces e transmissions.

Uso:
    python daily_update.py                          # modo interativo (products + orders)
    python daily_update.py --auto                   # modo automático (products + orders)
    python daily_update.py --auto --sku-marketplaces # inclui SKU marketplaces
    python daily_update.py --auto --transmissions    # inclui transmissions
    python daily_update.py --auto --all              # sincroniza tudo
"""

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from sqlalchemy import func
from app.database import engine, SessionLocal
from app import models
from app.anymarket_client import AnymarketClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_get(data: dict, key: str, default=None):
    """Extrai valor de dict de forma segura."""
    value = data.get(key, default)
    return value if value is not None else default


def parse_datetime(date_string):
    """Converte string ISO para datetime."""
    if not date_string:
        return None
    try:
        if date_string.endswith("Z"):
            date_string = date_string[:-1] + "+00:00"
        return datetime.fromisoformat(date_string)
    except (ValueError, TypeError):
        return None


def safe_int(value, default=0):
    """Converte para int de forma segura."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0):
    """Converte para float de forma segura."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Lookup: última data de cada entidade
# ---------------------------------------------------------------------------

def get_last_date(db, model_class, date_field="created_at", fallback_days=30):
    """Busca a última data de um campo em uma tabela."""
    try:
        col = getattr(model_class, date_field)
        last_record = (
            db.query(model_class)
            .filter(col.isnot(None))
            .order_by(col.desc())
            .first()
        )
        if last_record:
            last_date = getattr(last_record, date_field) + timedelta(seconds=1)
            logger.info(f"Ultimo registro de {model_class.__tablename__}: {getattr(last_record, date_field)}")
            return last_date

        default = datetime.now() - timedelta(days=fallback_days)
        logger.info(f"Nenhum registro em {model_class.__tablename__}, buscando desde {default}")
        return default
    except Exception as e:
        logger.error(f"Erro ao buscar ultima data de {model_class.__tablename__}: {e}")
        return datetime.now() - timedelta(days=7)


# ---------------------------------------------------------------------------
# Save: Products
# ---------------------------------------------------------------------------

def _build_product_fields(product_data):
    """Extrai todos os campos de um product da API para o model."""
    category = safe_get(product_data, "category", {})
    brand = safe_get(product_data, "brand", {})
    nbm = safe_get(product_data, "nbm", {})
    origin = safe_get(product_data, "origin", {})

    # Images
    images = safe_get(product_data, "images", [])
    first_image = images[0] if images else {}
    main_image_url = ""
    for img in images:
        if img.get("main", False):
            main_image_url = img.get("url", "")
            break
    if not main_image_url and images:
        main_image_url = images[0].get("url", "")

    # SKUs
    skus = safe_get(product_data, "skus", [])
    first_sku = skus[0] if skus else {}
    prices = [float(s.get("price", 0)) for s in skus if s.get("price")]
    amounts = [int(s.get("amount", 0)) for s in skus if s.get("amount")]
    total_stock = sum(amounts) if amounts else 0

    # Characteristics
    characteristics = safe_get(product_data, "characteristics", [])
    first_char = characteristics[0] if characteristics else {}

    return {
        "anymarket_id": str(safe_get(product_data, "id", "")),
        "title": safe_get(product_data, "title", ""),
        "description": safe_get(product_data, "description", ""),
        "external_id_product": safe_get(product_data, "externalIdProduct", ""),

        "category_id": str(safe_get(category, "id", "")),
        "category_name": safe_get(category, "name", ""),
        "category_path": safe_get(category, "path", ""),

        "brand_id": str(safe_get(brand, "id", "")),
        "brand_name": safe_get(brand, "name", ""),
        "brand_reduced_name": safe_get(brand, "reducedName", ""),
        "brand_partner_id": safe_get(brand, "partnerId", ""),

        "nbm_id": safe_get(nbm, "id", ""),
        "nbm_description": safe_get(nbm, "description", ""),

        "origin_id": str(safe_get(origin, "id", "")),
        "origin_description": safe_get(origin, "description", ""),

        "model": safe_get(product_data, "model", ""),
        "video_url": safe_get(product_data, "videoUrl", ""),
        "gender": safe_get(product_data, "gender", ""),

        "warranty_time": safe_int(product_data.get("warrantyTime")),
        "warranty_text": safe_get(product_data, "warrantyText", ""),

        "height": safe_float(product_data.get("height")),
        "width": safe_float(product_data.get("width")),
        "weight": safe_float(product_data.get("weight")),
        "length": safe_float(product_data.get("length")),

        "price_factor": safe_float(product_data.get("priceFactor")),
        "calculated_price": bool(safe_get(product_data, "calculatedPrice", False)),
        "definition_price_scope": safe_get(product_data, "definitionPriceScope", ""),

        "has_variations": bool(safe_get(product_data, "hasVariations", False)),
        "is_product_active": bool(safe_get(product_data, "isProductActive", True)),
        "product_type": safe_get(product_data, "type", ""),
        "allow_automatic_sku_marketplace_creation": bool(safe_get(product_data, "allowAutomaticSkuMarketplaceCreation", True)),

        # Images expandidas
        "image_id": str(safe_get(first_image, "id", "")),
        "image_index": safe_int(first_image.get("index")),
        "image_main": bool(safe_get(first_image, "main", False)),
        "image_url": safe_get(first_image, "url", ""),
        "image_thumbnail_url": safe_get(first_image, "thumbnailUrl", ""),
        "image_low_resolution_url": safe_get(first_image, "lowResolutionUrl", ""),
        "image_standard_url": safe_get(first_image, "standardUrl", ""),
        "image_original_image": safe_get(first_image, "originalImage", ""),
        "image_status": safe_get(first_image, "status", ""),
        "image_standard_width": safe_int(first_image.get("standardWidth")),
        "image_standard_height": safe_int(first_image.get("standardHeight")),
        "image_original_width": safe_int(first_image.get("originalWidth")),
        "image_original_height": safe_int(first_image.get("originalHeight")),
        "image_product_id": str(safe_get(first_image, "productId", "")),
        "total_images": len(images),
        "has_main_image": any(img.get("main", False) for img in images),
        "main_image_url": main_image_url,

        # SKUs expandidos
        "sku_id": str(safe_get(first_sku, "id", "")),
        "sku_title": safe_get(first_sku, "title", ""),
        "sku_partner_id": safe_get(first_sku, "partnerId", ""),
        "sku_ean": safe_get(first_sku, "ean", ""),
        "sku_price": safe_float(first_sku.get("price")),
        "sku_amount": safe_int(first_sku.get("amount")),
        "sku_additional_time": safe_int(first_sku.get("additionalTime")),
        "sku_stock_local_id": str(safe_get(first_sku, "stockLocalId", "")),
        "total_skus": len(skus),
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "total_stock": total_stock,
        "avg_price": sum(prices) / len(prices) if prices else None,
        "has_stock": total_stock > 0,

        # Characteristics expandidas
        "characteristic_index": safe_int(first_char.get("index")),
        "characteristic_name": safe_get(first_char, "name", ""),
        "characteristic_value": safe_get(first_char, "value", ""),
        "total_characteristics": len(characteristics),
        "has_characteristics": len(characteristics) > 0,

        # Campos legados
        "sku": safe_get(first_sku, "partnerId", ""),
        "price": safe_float(first_sku.get("price")),
        "stock_quantity": safe_int(first_sku.get("amount")),
        "active": bool(safe_get(product_data, "isProductActive", True)),

        # JSON completos
        "characteristics": characteristics,
        "images": images,
        "skus": skus,

        "sync_status": "synced",
        "last_sync_date": datetime.now(),
    }


def save_products(products_data, db):
    """Salva/atualiza produtos no banco."""
    for product_data in products_data:
        try:
            fields = _build_product_fields(product_data)
            anymarket_id = fields["anymarket_id"]

            existing = db.query(models.Product).filter(
                models.Product.anymarket_id == anymarket_id
            ).first()

            if existing:
                for k, v in fields.items():
                    if k != "anymarket_id":
                        setattr(existing, k, v)
                existing.updated_at = datetime.now()
                logger.info(f"Product atualizado: {anymarket_id}")
            else:
                db.add(models.Product(**fields))
                logger.info(f"Product criado: {anymarket_id}")

        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar product {product_data.get('id')}: {e}")
            continue

    db.commit()


# ---------------------------------------------------------------------------
# Save: Orders
# ---------------------------------------------------------------------------

def _build_order_fields(order_data):
    """Extrai todos os campos de um order da API para o model."""
    quote_reconciliation = safe_get(order_data, "quoteReconciliation", {})
    invoice = safe_get(order_data, "invoice", {})
    shipping = safe_get(order_data, "shipping", {})
    billing_address = safe_get(order_data, "billingAddress", {})
    anymarket_addr = safe_get(order_data, "anymarketAddress", {})
    buyer = safe_get(order_data, "buyer", {})
    tracking = safe_get(order_data, "tracking", {})
    pickup = safe_get(order_data, "pickup", {})
    metadata = safe_get(order_data, "metadata", {})

    # Items
    items = safe_get(order_data, "items", [])
    first_item = items[0] if items else {}
    item_product = safe_get(first_item, "product", {})
    item_sku = safe_get(first_item, "sku", {})
    item_shippings = safe_get(first_item, "shippings", [])
    first_item_shipping = item_shippings[0] if item_shippings else {}
    item_stocks = safe_get(first_item, "stocks", [])
    first_item_stock = item_stocks[0] if item_stocks else {}

    # Payments
    payments = safe_get(order_data, "payments", [])
    first_payment = payments[0] if payments else {}

    return {
        "anymarket_id": str(safe_get(order_data, "id", "")),
        "account_name": safe_get(order_data, "accountName", ""),
        "market_place_id": safe_get(order_data, "marketPlaceId", ""),
        "market_place_number": safe_get(order_data, "marketPlaceNumber", ""),
        "partner_id": safe_get(order_data, "partnerId", ""),
        "marketplace": safe_get(order_data, "marketPlace", ""),
        "sub_channel": safe_get(order_data, "subChannel", ""),
        "sub_channel_normalized": safe_get(order_data, "subChannelNormalized", ""),

        "created_at_anymarket": parse_datetime(safe_get(order_data, "createdAt")),
        "payment_date": parse_datetime(safe_get(order_data, "paymentDate")),
        "cancel_date": parse_datetime(safe_get(order_data, "cancelDate")),

        "shipping_option_id": safe_get(order_data, "shippingOptionId", ""),
        "transmission_status": safe_get(order_data, "transmissionStatus", ""),
        "status": safe_get(order_data, "status", ""),
        "market_place_status": safe_get(order_data, "marketPlaceStatus", ""),
        "market_place_status_complement": safe_get(order_data, "marketPlaceStatusComplement", ""),
        "market_place_shipment_status": safe_get(order_data, "marketPlaceShipmentStatus", ""),

        "document_intermediator": safe_get(order_data, "documentIntermediator", ""),
        "intermediate_registration_id": safe_get(order_data, "intermediateRegistrationId", ""),
        "document_payment_institution": safe_get(order_data, "documentPaymentInstitution", ""),
        "fulfillment": bool(safe_get(order_data, "fulfillment", False)),

        "quote_id": safe_get(quote_reconciliation, "quoteId", ""),
        "quote_price": safe_float(quote_reconciliation.get("price")),

        "discount": safe_float(order_data.get("discount")),
        "freight": safe_float(order_data.get("freight")),
        "seller_freight": safe_float(order_data.get("sellerFreight")),
        "interest_value": safe_float(order_data.get("interestValue")),
        "gross": safe_float(order_data.get("gross")),
        "total": safe_float(order_data.get("total")),

        "market_place_url": safe_get(order_data, "marketPlaceUrl", ""),

        # Invoice
        "invoice_access_key": safe_get(invoice, "accessKey", ""),
        "invoice_series": safe_get(invoice, "series", ""),
        "invoice_number": safe_get(invoice, "number", ""),
        "invoice_date": parse_datetime(safe_get(invoice, "date")),
        "invoice_cfop": safe_get(invoice, "cfop", ""),
        "invoice_company_state_tax_id": safe_get(invoice, "companyStateTaxId", ""),
        "invoice_link_nfe": safe_get(invoice, "linkNfe", ""),
        "invoice_link": safe_get(invoice, "invoiceLink", ""),
        "invoice_extra_description": safe_get(invoice, "extraDescription", ""),

        # Shipping
        "shipping_address": safe_get(shipping, "address", ""),
        "shipping_city": safe_get(shipping, "city", ""),
        "shipping_comment": safe_get(shipping, "comment", ""),
        "shipping_country": safe_get(shipping, "country", ""),
        "shipping_country_acronym_normalized": safe_get(shipping, "countryAcronymNormalized", ""),
        "shipping_country_name_normalized": safe_get(shipping, "countryNameNormalized", ""),
        "shipping_neighborhood": safe_get(shipping, "neighborhood", ""),
        "shipping_number": safe_get(shipping, "number", ""),
        "shipping_promised_shipping_time": parse_datetime(safe_get(shipping, "promisedShippingTime")),
        "shipping_promised_dispatch_time": parse_datetime(safe_get(shipping, "promisedDispatchTime")),
        "shipping_receiver_name": safe_get(shipping, "receiverName", ""),
        "shipping_reference": safe_get(shipping, "reference", ""),
        "shipping_state": safe_get(shipping, "state", ""),
        "shipping_state_name_normalized": safe_get(shipping, "stateNameNormalized", ""),
        "shipping_street": safe_get(shipping, "street", ""),
        "shipping_zip_code": safe_get(shipping, "zipCode", ""),

        # Billing address
        "billing_address": safe_get(billing_address, "address", ""),
        "billing_city": safe_get(billing_address, "city", ""),
        "billing_comment": safe_get(billing_address, "comment", ""),
        "billing_country": safe_get(billing_address, "country", ""),
        "billing_country_acronym_normalized": safe_get(billing_address, "countryAcronymNormalized", ""),
        "billing_country_name_normalized": safe_get(billing_address, "countryNameNormalized", ""),
        "billing_neighborhood": safe_get(billing_address, "neighborhood", ""),
        "billing_number": safe_get(billing_address, "number", ""),
        "billing_reference": safe_get(billing_address, "reference", ""),
        "billing_shipment_user_document": safe_get(billing_address, "shipmentUserDocument", ""),
        "billing_shipment_user_document_type": safe_get(billing_address, "shipmentUserDocumentType", ""),
        "billing_shipment_user_name": safe_get(billing_address, "shipmentUserName", ""),
        "billing_state": safe_get(billing_address, "state", ""),
        "billing_state_name_normalized": safe_get(billing_address, "stateNameNormalized", ""),
        "billing_street": safe_get(billing_address, "street", ""),
        "billing_zip_code": safe_get(billing_address, "zipCode", ""),

        # Anymarket address
        "anymarket_address": safe_get(anymarket_addr, "address", ""),
        "anymarket_city": safe_get(anymarket_addr, "city", ""),
        "anymarket_comment": safe_get(anymarket_addr, "comment", ""),
        "anymarket_country": safe_get(anymarket_addr, "country", ""),
        "anymarket_neighborhood": safe_get(anymarket_addr, "neighborhood", ""),
        "anymarket_number": safe_get(anymarket_addr, "number", ""),
        "anymarket_promised_shipping_time": parse_datetime(safe_get(anymarket_addr, "promisedShippingTime")),
        "anymarket_receiver_name": safe_get(anymarket_addr, "receiverName", ""),
        "anymarket_reference": safe_get(anymarket_addr, "reference", ""),
        "anymarket_state": safe_get(anymarket_addr, "state", ""),
        "anymarket_state_acronym_normalized": safe_get(anymarket_addr, "stateAcronymNormalized", ""),
        "anymarket_street": safe_get(anymarket_addr, "street", ""),
        "anymarket_zip_code": safe_get(anymarket_addr, "zipCode", ""),

        # Buyer
        "buyer_cell_phone": safe_get(buyer, "cellPhone", ""),
        "buyer_document": safe_get(buyer, "document", ""),
        "buyer_document_number_normalized": safe_get(buyer, "documentNumberNormalized", ""),
        "buyer_document_type": safe_get(buyer, "documentType", ""),
        "buyer_email": safe_get(buyer, "email", ""),
        "buyer_market_place_id": safe_get(buyer, "marketPlaceId", ""),
        "buyer_name": safe_get(buyer, "name", ""),
        "buyer_phone": safe_get(buyer, "phone", ""),
        "buyer_date_of_birth": parse_datetime(safe_get(buyer, "dateOfBirth")),
        "buyer_company_state_tax_id": safe_get(buyer, "companyStateTaxId", ""),

        # Tracking
        "tracking_carrier": safe_get(tracking, "carrier", ""),
        "tracking_date": parse_datetime(safe_get(tracking, "date")),
        "tracking_delivered_date": parse_datetime(safe_get(tracking, "deliveredDate")),
        "tracking_estimate_date": parse_datetime(safe_get(tracking, "estimateDate")),
        "tracking_number": safe_get(tracking, "number", ""),
        "tracking_shipped_date": parse_datetime(safe_get(tracking, "shippedDate")),
        "tracking_url": safe_get(tracking, "url", ""),
        "tracking_carrier_document": safe_get(tracking, "carrierDocument", ""),
        "tracking_buffering_date": parse_datetime(safe_get(tracking, "bufferingDate")),
        "tracking_delivery_status": safe_get(tracking, "deliveryStatus", ""),

        # Pickup
        "pickup_id": safe_int(pickup.get("id")),
        "pickup_description": safe_get(pickup, "description", ""),
        "pickup_partner_id": safe_int(pickup.get("partnerId")),
        "pickup_marketplace_id": safe_get(pickup, "marketplaceId", ""),
        "pickup_receiver_name": safe_get(pickup, "receiverName", ""),

        "id_account": safe_int(order_data.get("idAccount")),

        # Metadata
        "metadata_number_of_packages": safe_get(metadata, "number-of-packages", ""),
        "metadata_cd_zip_code": safe_get(metadata, "cdZipCode", ""),
        "metadata_need_invoice_xml": safe_get(metadata, "needInvoiceXML", ""),
        "metadata_mshops": safe_get(metadata, "mshops", ""),
        "metadata_envvias": safe_get(metadata, "Envvias", ""),
        "metadata_via_total_discount_amount": safe_get(metadata, "VIAtotalDiscountAmount", ""),
        "metadata_b2w_shipping_type": safe_get(metadata, "B2WshippingType", ""),
        "metadata_logistic_type": safe_get(metadata, "logistic_type", ""),
        "metadata_print_tag": safe_get(metadata, "printTag", ""),
        "metadata_cancel_detail_motivation": safe_get(metadata, "canceldetail_motivation", ""),
        "metadata_cancel_detail_code": safe_get(metadata, "canceldetail_code", ""),
        "metadata_cancel_detail_description": safe_get(metadata, "canceldetail_description", ""),
        "metadata_cancel_detail_requested_by": safe_get(metadata, "canceldetail_requested_by", ""),
        "metadata_order_type_name": safe_get(metadata, "orderTypeName", ""),
        "metadata_shipping_id": safe_get(metadata, "shippingId", ""),

        # Items expandidos
        "item_product_id": str(safe_get(item_product, "id", "")),
        "item_product_title": safe_get(item_product, "title", ""),
        "item_sku_id": str(safe_get(item_sku, "id", "")),
        "item_sku_title": safe_get(item_sku, "title", ""),
        "item_sku_partner_id": safe_get(item_sku, "partnerId", ""),
        "item_sku_ean": safe_get(item_sku, "ean", ""),
        "item_amount": safe_float(first_item.get("amount")),
        "item_unit": safe_float(first_item.get("unit")),
        "item_gross": safe_float(first_item.get("gross")),
        "item_total": safe_float(first_item.get("total")),
        "item_discount": safe_float(first_item.get("discount")),
        "item_id_in_marketplace": safe_get(first_item, "idInMarketPlace", ""),
        "item_order_item_id": str(safe_get(first_item, "orderItemId", "")),
        "item_free_shipping": bool(safe_get(first_item, "freeShipping", False)),
        "item_is_catalog": bool(safe_get(first_item, "isCatalog", False)),
        "item_id_in_marketplace_catalog_origin": safe_get(first_item, "idInMarketplaceCatalogOrigin", ""),
        "item_shipping_id": str(safe_get(first_item_shipping, "id", "")),
        "item_shipping_type": safe_get(first_item_shipping, "shippingtype", ""),
        "item_shipping_carrier_normalized": safe_get(first_item_shipping, "shippingCarrierNormalized", ""),
        "item_shipping_carrier_type_normalized": safe_get(first_item_shipping, "shippingCarrierTypeNormalized", ""),
        "item_stock_local_id": str(safe_get(first_item_stock, "stockLocalId", "")),
        "item_stock_amount": safe_float(first_item_stock.get("amount")),
        "item_stock_name": safe_get(first_item_stock, "stockName", ""),
        "total_items": len(items),
        "total_items_amount": sum(float(i.get("amount", 0)) for i in items),
        "total_items_value": sum(float(i.get("total", 0)) for i in items),

        # Payments expandidos
        "payment_method": safe_get(first_payment, "method", ""),
        "payment_status": safe_get(first_payment, "status", ""),
        "payment_value": safe_float(first_payment.get("value")),
        "payment_marketplace_id": safe_get(first_payment, "marketplaceId", ""),
        "payment_method_normalized": safe_get(first_payment, "paymentMethodNormalized", ""),
        "payment_detail_normalized": safe_get(first_payment, "paymentDetailNormalized", ""),
        "total_payments": len(payments),
        "total_payments_value": sum(float(p.get("value", 0)) for p in payments),

        # JSON completos
        "items_data": items,
        "payments_data": payments,
        "shippings_data": safe_get(order_data, "shippings", []),
        "stocks_data": safe_get(order_data, "stocks", []),
        "metadata_extra": metadata,
    }


def save_orders(orders_data, db):
    """Salva/atualiza orders no banco."""
    for order_data in orders_data:
        try:
            fields = _build_order_fields(order_data)
            anymarket_id = fields["anymarket_id"]

            existing = db.query(models.Order).filter(
                models.Order.anymarket_id == anymarket_id
            ).first()

            if existing:
                for k, v in fields.items():
                    if k != "anymarket_id":
                        setattr(existing, k, v)
                existing.updated_at = datetime.now()
                logger.info(f"Order atualizado: {anymarket_id}")
            else:
                db.add(models.Order(**fields))
                logger.info(f"Order criado: {anymarket_id}")

        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar order {order_data.get('id')}: {e}")
            continue

    db.commit()


# ---------------------------------------------------------------------------
# Save: SKU Marketplaces
# ---------------------------------------------------------------------------

def _build_sku_marketplace_fields(sku_data):
    """Extrai campos de SKU marketplace da API para o model."""
    fields = safe_get(sku_data, "fields", {})
    attributes = safe_get(sku_data, "attributes", {})
    warnings = safe_get(sku_data, "warnings", [])

    return {
        "anymarket_id": str(safe_get(sku_data, "id", "")),
        "account_name": safe_get(sku_data, "accountName", ""),
        "id_account": safe_int(sku_data.get("idAccount")),
        "marketplace": safe_get(sku_data, "marketPlace", ""),
        "id_in_marketplace": safe_get(sku_data, "idInMarketplace", ""),
        "index": safe_int(sku_data.get("index")),
        "publication_status": safe_get(sku_data, "publicationStatus", ""),
        "marketplace_status": safe_get(sku_data, "marketplaceStatus", ""),
        "price": safe_float(sku_data.get("price")),
        "price_factor": safe_float(sku_data.get("priceFactor")),
        "discount_price": safe_float(sku_data.get("discountPrice")),
        "permalink": safe_get(sku_data, "permalink", ""),
        "sku_in_marketplace": safe_get(sku_data, "skuInMarketplace", ""),
        "marketplace_item_code": safe_get(sku_data, "marketplaceItemCode", ""),

        # Fields expandidos
        "field_title": safe_get(fields, "title", ""),
        "field_template": safe_int(fields.get("template")),
        "field_price_factor": safe_get(fields, "priceFactor", ""),
        "field_discount_type": safe_get(fields, "DISCOUNT_TYPE", ""),
        "field_discount_value": safe_get(fields, "DISCOUNT_VALUE", ""),
        "field_has_discount": bool(safe_get(fields, "HAS_DISCOUNT", False)),
        "field_concat_attributes": safe_get(fields, "CONCAT_ATTRIBUTES", ""),
        "field_delivery_type": safe_get(fields, "delivery_type", ""),
        "field_shipment": safe_get(fields, "SHIPMENT", ""),
        "field_cross_docking": safe_get(fields, "crossDocking", ""),
        "field_custom_description": safe_get(fields, "CUSTOM_DESCRIPTION", ""),
        "field_ean": safe_get(fields, "EAN", ""),
        "field_manufacturing_time": safe_get(fields, "MANUFACTURING_TIME", ""),
        "field_value": safe_get(fields, "VALUE", ""),
        "field_percent": safe_get(fields, "PERCENT", ""),
        "field_bronze_price": safe_get(fields, "bronze_price", ""),
        "field_bronze_price_factor": safe_get(fields, "bronze_price_factor", ""),
        "field_silver_price": safe_get(fields, "silver_price", ""),
        "field_silver_price_factor": safe_get(fields, "silver_price_factor", ""),
        "field_gold_price": safe_get(fields, "gold_price", ""),
        "field_gold_price_factor": safe_get(fields, "gold_price_factor", ""),
        "field_gold_premium_price": safe_get(fields, "gold_premium_price", ""),
        "field_gold_premium_price_factor": safe_get(fields, "gold_premium_price_factor", ""),
        "field_gold_pro_price": safe_get(fields, "gold_pro_price", ""),
        "field_gold_pro_price_factor": safe_get(fields, "gold_pro_price_factor", ""),
        "field_gold_special_price": safe_get(fields, "gold_special_price", ""),
        "field_gold_special_price_factor": safe_get(fields, "gold_special_price_factor", ""),
        "field_free_price": safe_get(fields, "free_price", ""),
        "field_free_price_factor": safe_get(fields, "free_price_factor", ""),
        "field_buying_mode": safe_get(fields, "buying_mode", ""),
        "field_category_with_variation": safe_get(fields, "category_with_variation", ""),
        "field_condition": safe_get(fields, "condition", ""),
        "field_free_shipping": bool(safe_get(fields, "free_shipping", False)),
        "field_listing_type_id": safe_get(fields, "listing_type_id", ""),
        "field_shipping_local_pick_up": bool(safe_get(fields, "shipping_local_pick_up", False)),
        "field_shipping_mode": safe_get(fields, "shipping_mode", ""),
        "field_measurement_chart_id": safe_get(fields, "measurement_chart_id", ""),
        "field_warranty_time": safe_get(fields, "warranty_time", ""),
        "field_has_fulfillment": bool(safe_get(fields, "HAS_FULFILLMENT", False)),
        "field_official_store_id": safe_get(fields, "official_store_id", ""),
        "field_ml_channels": safe_get(fields, "ml_channels", ""),
        "field_is_main_sku": bool(safe_get(fields, "is_main_sku", False)),
        "field_is_match": bool(safe_get(fields, "is_match", False)),

        "warnings_count": len(warnings),
        "has_warnings": len(warnings) > 0,

        "fields_data": fields if fields else None,
        "attributes_data": attributes if attributes else None,
        "warnings_data": warnings if warnings else None,

        "sync_status": "synced",
        "last_sync_date": datetime.now(),
    }


def save_sku_marketplaces(sku_marketplaces_data, db):
    """Salva/atualiza SKU marketplaces no banco."""
    for sku_data in sku_marketplaces_data:
        try:
            fields = _build_sku_marketplace_fields(sku_data)
            anymarket_id = fields["anymarket_id"]

            if not anymarket_id:
                continue

            existing = db.query(models.SkuMarketplace).filter(
                models.SkuMarketplace.anymarket_id == anymarket_id
            ).first()

            if existing:
                for k, v in fields.items():
                    if k != "anymarket_id":
                        setattr(existing, k, v)
                existing.updated_at = datetime.now()
                logger.info(f"SKU marketplace atualizado: {anymarket_id}")
            else:
                db.add(models.SkuMarketplace(**fields))
                logger.info(f"SKU marketplace criado: {anymarket_id}")

        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar SKU marketplace {sku_data.get('id')}: {e}")
            continue

    db.commit()


# ---------------------------------------------------------------------------
# Save: Transmissions
# ---------------------------------------------------------------------------

def _build_transmission_fields(trans_data):
    """Extrai campos de transmission da API para o model."""
    category = safe_get(trans_data, "category", {})
    brand = safe_get(trans_data, "brand", {})
    product = safe_get(trans_data, "product", {})
    nbm = safe_get(trans_data, "nbm", {})
    origin = safe_get(trans_data, "origin", {})
    sku = safe_get(trans_data, "sku", {})
    characteristics = safe_get(trans_data, "characteristics", [])
    images = safe_get(trans_data, "images", [])

    variations = safe_get(sku, "variations", [])
    first_variation = variations[0] if variations else {}
    variation_type = safe_get(first_variation, "type", {})
    first_char = characteristics[0] if characteristics else {}
    first_image = images[0] if images else {}

    main_image_url = ""
    for img in images:
        if img.get("main", False):
            main_image_url = img.get("url", "")
            break
    if not main_image_url and images:
        main_image_url = images[0].get("url", "")

    return {
        "anymarket_id": str(safe_get(trans_data, "id", "")),
        "account_name": safe_get(trans_data, "accountName", ""),
        "description": safe_get(trans_data, "description", ""),
        "model": safe_get(trans_data, "model", ""),
        "video_url": safe_get(trans_data, "videoUrl", ""),
        "warranty_time": safe_int(trans_data.get("warrantyTime")),
        "warranty_text": safe_get(trans_data, "warrantyText", ""),

        "height": safe_float(trans_data.get("height")),
        "width": safe_float(trans_data.get("width")),
        "weight": safe_float(trans_data.get("weight")),
        "length": safe_float(trans_data.get("length")),

        "status": safe_get(trans_data, "status", ""),
        "transmission_message": safe_get(trans_data, "transmissionMessage", ""),
        "publication_status": safe_get(trans_data, "publicationStatus", ""),
        "marketplace_status": safe_get(trans_data, "marketPlaceStatus", ""),
        "price_factor": safe_float(trans_data.get("priceFactor")),

        "category_id": str(safe_get(category, "id", "")),
        "category_name": safe_get(category, "name", ""),
        "category_path": safe_get(category, "path", ""),

        "brand_id": str(safe_get(brand, "id", "")),
        "brand_name": safe_get(brand, "name", ""),

        "product_id": str(safe_get(product, "id", "")),
        "product_title": safe_get(product, "title", ""),

        "nbm_id": safe_get(nbm, "id", ""),
        "nbm_description": safe_get(nbm, "description", ""),

        "origin_id": str(safe_get(origin, "id", "")),
        "origin_description": safe_get(origin, "description", ""),

        "sku_id": str(safe_get(sku, "id", "")),
        "sku_title": safe_get(sku, "title", ""),
        "sku_partner_id": safe_get(sku, "partnerId", ""),
        "sku_ean": safe_get(sku, "ean", ""),
        "sku_price": safe_float(sku.get("price")),
        "sku_amount": safe_int(sku.get("amount")),
        "sku_discount_price": safe_float(sku.get("discountPrice")),

        "variation_id": str(safe_get(first_variation, "id", "")),
        "variation_description": safe_get(first_variation, "description", ""),
        "variation_type_id": str(safe_get(variation_type, "id", "")),
        "variation_type_name": safe_get(variation_type, "name", ""),
        "variation_visual": bool(safe_get(variation_type, "visualVariation", False)),
        "total_variations": len(variations),

        "characteristic_index": safe_int(first_char.get("index")),
        "characteristic_name": safe_get(first_char, "name", ""),
        "characteristic_value": safe_get(first_char, "value", ""),
        "total_characteristics": len(characteristics),

        "image_id": str(safe_get(first_image, "id", "")),
        "image_index": safe_int(first_image.get("index")),
        "image_main": bool(safe_get(first_image, "main", False)),
        "image_url": safe_get(first_image, "url", ""),
        "image_thumbnail_url": safe_get(first_image, "thumbnailUrl", ""),
        "image_status": safe_get(first_image, "status", ""),
        "image_status_message": safe_get(first_image, "statusMessage", ""),
        "total_images": len(images),
        "main_image_url": main_image_url,

        "category_data": category if category else None,
        "brand_data": brand if brand else None,
        "product_data": product if product else None,
        "nbm_data": nbm if nbm else None,
        "origin_data": origin if origin else None,
        "sku_data": sku if sku else None,
        "characteristics_data": characteristics if characteristics else None,
        "images_data": images if images else None,

        "sync_status": "synced",
        "last_sync_date": datetime.now(),
    }


def save_transmissions(transmissions_data, db):
    """Salva/atualiza transmissions no banco."""
    for trans_data in transmissions_data:
        try:
            fields = _build_transmission_fields(trans_data)
            anymarket_id = fields["anymarket_id"]

            if not anymarket_id:
                continue

            existing = db.query(models.Transmission).filter(
                models.Transmission.anymarket_id == anymarket_id
            ).first()

            if existing:
                for k, v in fields.items():
                    if k != "anymarket_id":
                        setattr(existing, k, v)
                existing.updated_at = datetime.now()
                logger.info(f"Transmission atualizado: {anymarket_id}")
            else:
                db.add(models.Transmission(**fields))
                logger.info(f"Transmission criado: {anymarket_id}")

        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar transmission {trans_data.get('id')}: {e}")
            continue

    db.commit()


# ---------------------------------------------------------------------------
# Update: paginacao generica + entidades especificas
# ---------------------------------------------------------------------------

def _paginate_and_save(client_method, save_fn, db, entity_name, filter_fn=None):
    """
    Loop generico de paginacao: busca paginas da API e salva no banco.
    filter_fn: funcao opcional para filtrar registros (ex: por data).
    Retorna total de registros processados.
    """
    offset = 0
    limit = 50
    total = 0

    while True:
        logger.info(f"Buscando {entity_name}: offset {offset}")
        response = client_method(limit=limit, offset=offset)

        # A API retorna {content: [...]} ou lista direta
        if isinstance(response, dict):
            records = response.get("content", [])
        else:
            records = response

        if not records:
            break

        if filter_fn:
            records = [r for r in records if filter_fn(r)]
            if not records:
                break

        save_fn(records, db)
        total += len(records)
        offset += limit

        logger.info(f"{entity_name}: {total} processados ate agora")

        if len(records) < limit:
            break

        time.sleep(0.5)

    logger.info(f"{entity_name}: concluido! Total: {total}")
    return total


def update_products(client, db):
    """Atualiza produtos novos desde a ultima sincronizacao."""
    since = get_last_date(db, models.Product)

    def is_new(product):
        dt = parse_datetime(product.get("createdAt"))
        return dt and dt >= since

    return _paginate_and_save(client.get_products, save_products, db, "products", filter_fn=is_new)


def update_orders(client, db):
    """Atualiza pedidos novos desde a ultima sincronizacao."""
    since = get_last_date(db, models.Order)

    def is_new(order):
        dt = parse_datetime(order.get("createdAt"))
        return dt and dt >= since

    return _paginate_and_save(client.get_orders, save_orders, db, "orders", filter_fn=is_new)


def update_sku_marketplaces(client, db):
    """Atualiza SKU marketplaces buscando por cada SKU existente no banco."""
    partner_ids = (
        db.query(models.Product.sku_partner_id)
        .filter(
            models.Product.sku_partner_id.isnot(None),
            models.Product.sku_partner_id != "",
        )
        .distinct()
        .all()
    )
    partner_ids = [p[0] for p in partner_ids if p[0]]
    logger.info(f"Encontrados {len(partner_ids)} SKUs para buscar marketplaces")

    total = 0
    for i, pid in enumerate(partner_ids):
        logger.info(f"[{i + 1}/{len(partner_ids)}] SKU marketplace para: {pid}")
        data = client.get_sku_marketplaces(partner_id=pid)
        if data:
            save_sku_marketplaces(data, db)
            total += len(data)
        time.sleep(0.5)

    logger.info(f"SKU marketplaces: concluido! Total: {total}")
    return total


def update_transmissions(client, db):
    """Atualiza todas as transmissions."""
    return _paginate_and_save(client.get_transmissions, save_transmissions, db, "transmissions")


# ---------------------------------------------------------------------------
# Summary & verification
# ---------------------------------------------------------------------------

def create_summary(results, start_time, end_time):
    """Cria JSON de resumo da sincronizacao."""
    try:
        duration = end_time - start_time
        summary = {
            "date": datetime.now().isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_formatted": str(duration),
            **{f"{k}_updated": v for k, v in results.items()},
            "total_records": sum(results.values()),
            "status": "success",
        }

        filename = f"daily_sync_summary_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"Resumo salvo: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Erro ao criar resumo: {e}")
        return None


def verify_sync_status(db):
    """Mostra estatisticas do banco."""
    try:
        yesterday = datetime.now() - timedelta(days=1)

        tables = [
            ("products", models.Product, "created_at"),
            ("orders", models.Order, "created_at"),
            ("sku_marketplaces", models.SkuMarketplace, "last_sync_date"),
            ("transmissions", models.Transmission, "last_sync_date"),
        ]

        stats = {}
        for name, model, recent_field in tables:
            total = db.query(model).count()
            col = getattr(model, recent_field)
            recent = db.query(model).filter(col >= yesterday).count()
            stats[name] = {"total": total, "recent_24h": recent}
            logger.info(f"  {name}: {total} total, {recent} recentes (24h)")

        return stats
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return None


# ---------------------------------------------------------------------------
# CLI & main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Atualizacao diaria - Anymarket Backend")
    parser.add_argument("--auto", action="store_true", help="Modo automatico (sem confirmacao)")
    parser.add_argument("--sku-marketplaces", action="store_true", help="Incluir sincronizacao de SKU marketplaces")
    parser.add_argument("--transmissions", action="store_true", help="Incluir sincronizacao de transmissions")
    parser.add_argument("--all", action="store_true", help="Sincronizar tudo (products + orders + sku_marketplaces + transmissions)")
    return parser.parse_args()


def main():
    args = parse_args()
    start_time = datetime.now()

    sync_sku = args.sku_marketplaces or args.all
    sync_trans = args.transmissions or args.all

    # Header
    print("ATUALIZACAO DIARIA - ANYMARKET BACKEND")
    print("=" * 60)
    print(f"Iniciada em: {start_time:%d/%m/%Y %H:%M:%S}")
    print()

    steps = ["1. Atualizar produtos", "2. Atualizar pedidos"]
    if sync_sku:
        steps.append(f"{len(steps) + 1}. Sincronizar SKU marketplaces")
    if sync_trans:
        steps.append(f"{len(steps) + 1}. Sincronizar transmissions")
    steps.append(f"{len(steps) + 1}. Gerar relatorio")

    for s in steps:
        print(f"  {s}")
    print()

    # Confirmacao manual
    if not args.auto:
        confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
        if confirm not in ("sim", "s", "yes", "y"):
            print("Operacao cancelada")
            return

    try:
        client = AnymarketClient()
        db = SessionLocal()

        logger.info("Status inicial do banco:")
        verify_sync_status(db)

        # Products
        print("\n" + "=" * 40)
        logger.info("ATUALIZANDO PRODUTOS...")
        results = {"products": update_products(client, db)}

        # Orders
        print("\n" + "=" * 40)
        logger.info("ATUALIZANDO PEDIDOS...")
        results["orders"] = update_orders(client, db)

        # SKU Marketplaces (opcional)
        if sync_sku:
            print("\n" + "=" * 40)
            logger.info("ATUALIZANDO SKU MARKETPLACES...")
            results["sku_marketplaces"] = update_sku_marketplaces(client, db)

        # Transmissions (opcional)
        if sync_trans:
            print("\n" + "=" * 40)
            logger.info("ATUALIZANDO TRANSMISSIONS...")
            results["transmissions"] = update_transmissions(client, db)

        # Status final
        print("\n" + "=" * 40)
        logger.info("Status final do banco:")
        final_stats = verify_sync_status(db)

        end_time = datetime.now()
        summary_file = create_summary(results, start_time, end_time)

        # Resultado
        print("\nATUALIZACAO DIARIA CONCLUIDA!")
        print("=" * 60)
        print(f"Iniciada:  {start_time:%d/%m/%Y %H:%M:%S}")
        print(f"Finalizada: {end_time:%d/%m/%Y %H:%M:%S}")
        print(f"Duracao:   {end_time - start_time}")
        print()

        for entity, count in results.items():
            print(f"  {entity}: {count} atualizados")
        print(f"  TOTAL: {sum(results.values())}")

        if summary_file:
            print(f"\nRelatorio: {summary_file}")

        if final_stats:
            print("\nEstatisticas do banco:")
            for name, info in final_stats.items():
                print(f"  {name}: {info['total']} total, {info['recent_24h']} recentes (24h)")

        print()
        print("Para automatizar:")
        print("  python daily_update.py --auto")
        print("  python daily_update.py --auto --all")
        print()
        print("Agendar no cron (todos os dias as 6h):")
        print("  0 6 * * * cd /caminho/para/projeto && python daily_update.py --auto")

        db.close()

    except Exception as e:
        logger.error(f"Erro durante a atualizacao: {e}")
        print(f"Atualizacao falhou: {e}")

        try:
            error_log = {
                "date": datetime.now().isoformat(),
                "error": str(e),
                **{f"{k}_updated": v for k, v in locals().get("results", {}).items()},
                "status": "error",
            }
            filename = f"daily_sync_error_{datetime.now():%Y%m%d_%H%M%S}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(error_log, f, indent=2, ensure_ascii=False)
            print(f"Log de erro: {filename}")
        except Exception:
            pass


if __name__ == "__main__":
    main()
