#!/usr/bin/env python3
"""
Script completo para migrar orders com TODOS os campos expandidos
Cada objeto aninhado vira colunas individuais na tabela
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

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

def save_orders_to_db_complete(orders_data, db):
    """
    Salva pedidos no banco de dados com TODOS os campos expandidos
    Cada objeto aninhado vira colunas individuais
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
            
            # Mapear TODOS os campos para colunas individuais
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
                
                # Dados JSON para arrays complexos (que não podem ser normalizados facilmente)
                "payments_data": safe_get_value(order_data, "payments", []),
                "items_data": safe_get_value(order_data, "items", []),
                "shippings_data": safe_get_value(order_data, "shippings", []),
                "stocks_data": safe_get_value(order_data, "stocks", []),
                "metadata_extra": metadata,  # Metadata completo para referência
            }
            
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

def reset_orders_table():
    """Reseta apenas a tabela de orders"""
    try:
        logger.info("🗑️  Resetando tabela 'orders'...")
        
        # Drop e recriar tabela
        models.Order.__table__.drop(bind=engine, checkfirst=True)
        models.Order.__table__.create(bind=engine)
        
        logger.info("✅ Tabela 'orders' resetada com estrutura COMPLETA")
        
    except Exception as e:
        logger.error(f"❌ Erro ao resetar tabela: {e}")
        raise

def import_all_orders():
    """Importa todos os orders da API Anymarket com estrutura completa"""
    try:
        logger.info("📥 Iniciando importação COMPLETA de orders...")
        
        # Instanciar cliente e sessão do banco
        client = AnymarketClient()
        db = SessionLocal()
        
        offset = 0
        limit = 50
        total_imported = 0
        
        while True:
            logger.info(f"🔍 Buscando orders: offset {offset}, limit {limit}")
            
            # Buscar orders da API
            orders_response = client.get_orders(limit=limit, offset=offset)
            orders = orders_response.get("content", [])
            
            if not orders:
                logger.info("📭 Nenhum order encontrado. Importação finalizada.")
                break
            
            logger.info(f"📦 Processando {len(orders)} orders...")
            
            # Salvar no banco usando a função COMPLETA
            save_orders_to_db_complete(orders, db)
            
            total_imported += len(orders)
            offset += limit
            
            logger.info(f"✅ Total importado até agora: {total_imported}")
            
            # Se retornou menos que o limite, não há mais orders
            if len(orders) < limit:
                break
            
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
        
        logger.info(f"🎉 Importação concluída! Total: {total_imported} orders")
        
        db.close()
        return total_imported
        
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        raise

def verify_complete_import():
    """Verifica se a importação com estrutura completa funcionou"""
    try:
        db = SessionLocal()
        
        # Contar total de orders
        total_count = db.query(models.Order).count()
        
        # Buscar alguns exemplos
        sample_orders = db.query(models.Order).limit(3).all()
        
        logger.info(f"📊 Verificação da importação COMPLETA:")
        logger.info(f"   - Total de orders: {total_count}")
        
        if sample_orders:
            logger.info(f"   - Estrutura COMPLETA verificada:")
            for order in sample_orders:
                logger.info(f"     • Order {order.anymarket_id}")
                
                # Verificar campos básicos
                logger.info(f"       Marketplace: {order.marketplace}")
                logger.info(f"       Status: {order.status}")
                logger.info(f"       Total: R$ {order.total}")
                
                # Verificar campos expandidos de endereço
                if order.shipping_street:
                    address = f"{order.shipping_street}, {order.shipping_number}"
                    if order.shipping_city:
                        address += f" - {order.shipping_city}/{order.shipping_state}"
                    logger.info(f"       Endereço: {address}")
                
                # Verificar comprador expandido
                if order.buyer_name:
                    buyer_info = f"{order.buyer_name}"
                    if order.buyer_email:
                        buyer_info += f" ({order.buyer_email})"
                    if order.buyer_phone:
                        buyer_info += f" - Tel: {order.buyer_phone}"
                    logger.info(f"       Comprador: {buyer_info}")
                
                # Verificar nota fiscal expandida
                if order.invoice_number:
                    invoice_info = f"NF: {order.invoice_number}"
                    if order.invoice_series:
                        invoice_info += f" Série: {order.invoice_series}"
                    if order.invoice_access_key:
                        invoice_info += f" Chave: {order.invoice_access_key[:20]}..."
                    logger.info(f"       {invoice_info}")
                
                # Verificar rastreamento expandido
                if order.tracking_number:
                    tracking_info = f"Rastreio: {order.tracking_number}"
                    if order.tracking_carrier:
                        tracking_info += f" ({order.tracking_carrier})"
                    logger.info(f"       {tracking_info}")
                
                # Verificar metadados expandidos
                metadata_fields = [
                    order.metadata_logistic_type,
                    order.metadata_order_type_name,
                    order.metadata_shipping_id
                ]
                metadata_present = [f for f in metadata_fields if f]
                if metadata_present:
                    logger.info(f"       Metadados: {len(metadata_present)} campos preenchidos")
                
                # Verificar dados JSON
                json_fields = [
                    ("Payments", order.payments_data),
                    ("Items", order.items_data),
                    ("Shippings", order.shippings_data),
                    ("Stocks", order.stocks_data)
                ]
                for field_name, field_data in json_fields:
                    if field_data:
                        logger.info(f"       {field_name} JSON: {len(field_data)} registros")
        
        db.close()
        return total_count
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return 0

def show_table_structure():
    """Mostra a estrutura da tabela orders"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        if 'orders' not in inspector.get_table_names():
            logger.error("❌ Tabela 'orders' não encontrada!")
            return
        
        columns = inspector.get_columns('orders')
        
        logger.info(f"📋 ESTRUTURA DA TABELA ORDERS:")
        logger.info(f"   Total de colunas: {len(columns)}")
        
        # Agrupar colunas por categoria
        categories = {
            "Básicos": ["id", "anymarket_id", "marketplace", "status", "total"],
            "Shipping": [col for col in [c['name'] for c in columns] if col.startswith('shipping_')],
            "Billing": [col for col in [c['name'] for c in columns] if col.startswith('billing_')],
            "Buyer": [col for col in [c['name'] for c in columns] if col.startswith('buyer_')],
            "Invoice": [col for col in [c['name'] for c in columns] if col.startswith('invoice_')],
            "Tracking": [col for col in [c['name'] for c in columns] if col.startswith('tracking_')],
            "Metadata": [col for col in [c['name'] for c in columns] if col.startswith('metadata_')],
            "JSON": [col for col in [c['name'] for c in columns] if col.endswith('_data')]
        }
        
        for category, fields in categories.items():
            if fields:
                logger.info(f"   {category}: {len(fields)} campos")
                
    except Exception as e:
        logger.error(f"❌ Erro ao verificar estrutura: {e}")

def main():
    """Função principal do script de migração completa"""
    print("🔄 MIGRAÇÃO COMPLETA DE ORDERS - ANYMARKET")
    print("=" * 50)
    print("Este script vai:")
    print("1. Resetar a tabela orders com estrutura COMPLETA")
    print("2. Importar todos os orders com TODOS os campos expandidos")
    print("3. Cada objeto aninhado vira colunas individuais")
    print("4. Verificar se a estrutura está correta")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Passo 1: Reset da tabela
        print("\n" + "="*30)
        reset_orders_table()
        
        # Passo 1.5: Mostrar estrutura
        print("\n" + "="*30)
        show_table_structure()
        
        # Passo 2: Importação
        print("\n" + "="*30)
        total_imported = import_all_orders()
        
        # Passo 3: Verificação
        print("\n" + "="*30)
        total_verified = verify_complete_import()
        
        # Resultado final
        print("\n" + "🎉 MIGRAÇÃO COMPLETA CONCLUÍDA! " + "🎉")
        print("=" * 50)
        print(f"📥 Orders importados: {total_imported}")
        print(f"✅ Orders verificados: {total_verified}")
        print("")
        print("💡 Estrutura COMPLETA implementada:")
        print("   ✅ Todos os objetos aninhados viram colunas individuais")
        print("   ✅ shipping.* → shipping_*")
        print("   ✅ buyer.* → buyer_*")
        print("   ✅ invoice.* → invoice_*")
        print("   ✅ tracking.* → tracking_*")
        print("   ✅ metadata.* → metadata_*")
        print("   ✅ Arrays complexos mantidos como JSON")
        print("")
        print("💡 Próximos passos:")
        print("   - Testar API: python -m app.main")
        print("   - Ver orders: http://localhost:8000/orders")
        print("   - Orders completos: http://localhost:8000/orders/full")
        print("   - Documentação: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"💥 Erro durante a migração: {e}")
        print(f"❌ Migração falhou: {e}")

if __name__ == "__main__":
    main()