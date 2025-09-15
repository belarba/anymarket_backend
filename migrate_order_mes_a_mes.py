#!/usr/bin/env python3
"""
Script para migrar orders mês a mês para 2025
Usa createdAfter e createdBefore para buscar dados mensais
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, date

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

def save_orders_to_db_ultra_complete_final(orders_data, db):
    """Salva pedidos no banco de dados com TODOS os campos expandidos"""
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
            
            # ITEMS expandidos
            items = safe_get_value(order_data, "items", [])
            first_item = items[0] if items else {}
            item_product = safe_get_value(first_item, "product", {})
            item_sku = safe_get_value(first_item, "sku", {})
            item_shippings = safe_get_value(first_item, "shippings", [])
            first_item_shipping = item_shippings[0] if item_shippings else {}
            item_stocks = safe_get_value(first_item, "stocks", [])
            first_item_stock = item_stocks[0] if item_stocks else {}
            
            # PAYMENTS expandidos
            payments = safe_get_value(order_data, "payments", [])
            first_payment = payments[0] if payments else {}
            
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
                "invoice_access_key": safe_get_value(invoice, "accessKey", ""),
                "invoice_series": safe_get_value(invoice, "series", ""),
                "invoice_number": safe_get_value(invoice, "number", ""),
                "invoice_date": parse_datetime(safe_get_value(invoice, "date")),
                "invoice_cfop": safe_get_value(invoice, "cfop", ""),
                "invoice_company_state_tax_id": safe_get_value(invoice, "companyStateTaxId", ""),
                "invoice_link_nfe": safe_get_value(invoice, "linkNfe", ""),
                "invoice_link": safe_get_value(invoice, "invoiceLink", ""),
                "invoice_extra_description": safe_get_value(invoice, "extraDescription", ""),
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
                "pickup_id": int(safe_get_value(pickup, "id", 0)) if pickup.get("id") else None,
                "pickup_description": safe_get_value(pickup, "description", ""),
                "pickup_partner_id": int(safe_get_value(pickup, "partnerId", 0)) if pickup.get("partnerId") else None,
                "pickup_marketplace_id": safe_get_value(pickup, "marketplaceId", ""),
                "pickup_receiver_name": safe_get_value(pickup, "receiverName", ""),
                "id_account": int(safe_get_value(order_data, "idAccount", 0)) if order_data.get("idAccount") else None,
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
                "item_product_id": str(safe_get_value(item_product, "id", "")),
                "item_product_title": safe_get_value(item_product, "title", ""),
                "item_sku_id": str(safe_get_value(item_sku, "id", "")),
                "item_sku_title": safe_get_value(item_sku, "title", ""),
                "item_sku_partner_id": safe_get_value(item_sku, "partnerId", ""),
                "item_sku_ean": safe_get_value(item_sku, "ean", ""),
                "item_amount": float(safe_get_value(first_item, "amount", 0)),
                "item_unit": float(safe_get_value(first_item, "unit", 0)),
                "item_gross": float(safe_get_value(first_item, "gross", 0)),
                "item_total": float(safe_get_value(first_item, "total", 0)),
                "item_discount": float(safe_get_value(first_item, "discount", 0)),
                "item_id_in_marketplace": safe_get_value(first_item, "idInMarketPlace", ""),
                "item_order_item_id": str(safe_get_value(first_item, "orderItemId", "")),
                "item_free_shipping": bool(safe_get_value(first_item, "freeShipping", False)),
                "item_is_catalog": bool(safe_get_value(first_item, "isCatalog", False)),
                "item_id_in_marketplace_catalog_origin": safe_get_value(first_item, "idInMarketplaceCatalogOrigin", ""),
                "item_shipping_id": str(safe_get_value(first_item_shipping, "id", "")),
                "item_shipping_type": safe_get_value(first_item_shipping, "shippingtype", ""),
                "item_shipping_carrier_normalized": safe_get_value(first_item_shipping, "shippingCarrierNormalized", ""),
                "item_shipping_carrier_type_normalized": safe_get_value(first_item_shipping, "shippingCarrierTypeNormalized", ""),
                "item_stock_local_id": str(safe_get_value(first_item_stock, "stockLocalId", "")),
                "item_stock_amount": float(safe_get_value(first_item_stock, "amount", 0)),
                "item_stock_name": safe_get_value(first_item_stock, "stockName", ""),
                "total_items": len(items),
                "total_items_amount": sum(float(item.get("amount", 0)) for item in items),
                "total_items_value": sum(float(item.get("total", 0)) for item in items),
                "payment_method": safe_get_value(first_payment, "method", ""),
                "payment_status": safe_get_value(first_payment, "status", ""),
                "payment_value": float(safe_get_value(first_payment, "value", 0)),
                "payment_marketplace_id": safe_get_value(first_payment, "marketplaceId", ""),
                "payment_method_normalized": safe_get_value(first_payment, "paymentMethodNormalized", ""),
                "payment_detail_normalized": safe_get_value(first_payment, "paymentDetailNormalized", ""),
                "total_payments": len(payments),
                "total_payments_value": sum(float(payment.get("value", 0)) for payment in payments),
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

def reset_orders_table():
    """Reseta tabela orders"""
    try:
        logger.info("🗑️  Resetando tabela 'orders'...")
        models.Order.__table__.drop(bind=engine, checkfirst=True)
        models.Order.__table__.create(bind=engine)
        logger.info("✅ Tabela 'orders' resetada")
    except Exception as e:
        logger.error(f"❌ Erro ao resetar tabela: {e}")
        raise

def get_orders_monthly(client, year, month, db):
    """Busca orders de um mês específico"""
    try:
        # Calcular primeiro e último dia do mês
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        # Formato ISO 8601 com timezone
        created_after = f"{year}-{month:02d}-01T00:00:00-03:00"
        created_before = f"{next_year}-{next_month:02d}-01T00:00:00-03:00"
        
        logger.info(f"📅 Buscando orders de {created_after} até {created_before}")
        
        offset = 0
        limit = 50
        total_monthly = 0
        
        while True:
            logger.info(f"🔍 Buscando orders: offset {offset}, limit {limit}")
            
            # Modificar client para aceitar parâmetros de data
            url = f"{client.base_url}/orders"
            params = {
                "limit": limit,
                "offset": offset,
                "createdAfter": created_after,
                "createdBefore": created_before
            }
            
            client._wait_for_rate_limit()
            
            import requests
            response = requests.get(url, headers=client.headers, params=params)
            
            if response.status_code == 429:
                logger.warning("Rate limit atingido. Aguardando 60 segundos...")
                time.sleep(60)
                response = requests.get(url, headers=client.headers, params=params)
            
            response.raise_for_status()
            orders_response = response.json()
            
            orders = orders_response.get("content", [])
            
            if not orders:
                logger.info(f"📭 Nenhum order encontrado para {created_after.strftime('%Y-%m')}")
                break
            
            logger.info(f"📦 Processando {len(orders)} orders...")
            save_orders_to_db_ultra_complete_final(orders, db)
            
            total_monthly += len(orders)
            offset += limit
            
            logger.info(f"✅ Total do mês até agora: {total_monthly}")
            
            if len(orders) < limit:
                break
            
            time.sleep(0.5)
        
        logger.info(f"✅ Mês {created_after.strftime('%Y-%m')} concluído: {total_monthly} orders")
        return total_monthly
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar orders do mês {month}: {e}")
        return 0

def import_orders_monthly():
    """Importa orders mês a mês para 2025"""
    try:
        logger.info("📥 Iniciando importação MÊS A MÊS de orders para 2025...")
        
        client = AnymarketClient()
        db = SessionLocal()
        
        year = 2025
        current_month = datetime.now().month
        total_imported = 0
        
        # Janeiro até mês atual
        for month in range(1, current_month + 1):
            logger.info(f"\n{'='*50}")
            logger.info(f"🗓️  PROCESSANDO MÊS {month:02d}/{year}")
            logger.info(f"{'='*50}")
            
            monthly_count = get_orders_monthly(client, year, month, db)
            total_imported += monthly_count
            
            logger.info(f"📊 Total geral até agora: {total_imported} orders")
        
        logger.info(f"\n🎉 Importação MÊS A MÊS concluída!")
        logger.info(f"📊 Total final: {total_imported} orders")
        
        db.close()
        return total_imported
        
    except Exception as e:
        logger.error(f"❌ Erro na importação mensal: {e}")
        raise

def verify_monthly_import():
    """Verifica importação mensal"""
    try:
        db = SessionLocal()
        
        total_count = db.query(models.Order).count()
        
        logger.info(f"📊 Verificação da importação MENSAL:")
        logger.info(f"   - Total de orders: {total_count}")
        
        # Orders por mês
        from sqlalchemy import func, extract
        monthly_stats = db.query(
            extract('month', models.Order.created_at_anymarket).label('month'),
            func.count(models.Order.id).label('count')
        ).filter(
            models.Order.created_at_anymarket.isnot(None),
            extract('year', models.Order.created_at_anymarket) == 2025
        ).group_by(
            extract('month', models.Order.created_at_anymarket)
        ).order_by('month').all()
        
        if monthly_stats:
            logger.info("   - Orders por mês em 2025:")
            for stat in monthly_stats:
                month_name = [
                    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
                ][int(stat.month)]
                logger.info(f"     {month_name}: {stat.count} orders")
        
        db.close()
        return total_count
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return 0

def main():
    """Função principal"""
    print("🔄 MIGRAÇÃO ORDERS MÊS A MÊS - 2025")
    print("=" * 60)
    print("Este script vai:")
    print("1. Resetar a tabela orders")
    print("2. Importar orders de Janeiro/2025 até hoje")
    print("3. Usar createdAfter e createdBefore para cada mês")
    print("4. Salvar com estrutura ultra completa")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Reset
        print("\n" + "="*30)
        reset_orders_table()
        
        # Importação mensal
        print("\n" + "="*30)
        total_imported = import_orders_monthly()
        
        # Verificação
        print("\n" + "="*30)
        total_verified = verify_monthly_import()
        
        print("\n" + "🎊 MIGRAÇÃO MENSAL CONCLUÍDA! " + "🎊")
        print("=" * 60)
        print(f"📥 Orders importados: {total_imported}")
        print(f"✅ Orders verificados: {total_verified}")
        print("")
        print("💡 Próximos passos:")
        print("   1. python -m app.main")
        print("   2. http://localhost:8000/orders")
        print("   3. http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"💥 Erro: {e}")
        print(f"❌ Migração falhou: {e}")

if __name__ == "__main__":
    main()