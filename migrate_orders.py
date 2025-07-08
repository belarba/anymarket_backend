#!/usr/bin/env python3
"""
Script completo para migrar orders:
1. Backup dos dados existentes (opcional)
2. Reset da tabela orders
3. Reimportação completa via API
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
# Remover import da função antiga - vamos usar a nova versão expandida
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_existing_orders():
    """Faz backup dos orders existentes em JSON"""
    try:
        db = SessionLocal()
        
        logger.info("💾 Fazendo backup dos orders existentes...")
        
        # Buscar todos os orders
        orders = db.query(models.Order).all()
        
        if not orders:
            logger.info("📭 Nenhum order encontrado para backup")
            db.close()
            return None
        
        # Converter para dict
        backup_data = []
        for order in orders:
            order_dict = {
                "id": order.id,
                "anymarket_id": order.anymarket_id,
                "marketplace": order.marketplace,
                "status": order.status,
                "total_amount": order.total_amount,
                "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "order_date": order.order_date.isoformat() if order.order_date else None,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            }
            backup_data.append(order_dict)
        
        # Salvar backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"orders_backup_{timestamp}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Backup salvo: {backup_filename} ({len(backup_data)} orders)")
        
        db.close()
        return backup_filename
        
    except Exception as e:
        logger.error(f"❌ Erro no backup: {e}")
        return None

def reset_orders_table():
    """Reseta apenas a tabela de orders"""
    try:
        logger.info("🗑️  Resetando tabela 'orders'...")
        
        # Drop e recriar tabela
        models.Order.__table__.drop(bind=engine, checkfirst=True)
        models.Order.__table__.create(bind=engine)
        
        logger.info("✅ Tabela 'orders' resetada")
        
    except Exception as e:
        logger.error(f"❌ Erro ao resetar tabela: {e}")
        raise

def safe_get_value(data: dict, key: str, default=None):
    """Função auxiliar para extrair valores de forma segura"""
    value = data.get(key, default)
    return value if value is not None else default

def parse_datetime(date_string):
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

def save_orders_to_db_expanded(orders_data, db):
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
            
            # Adicionar dados de endereço - AQUI ESTÁ O IMPORTANTE!
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

def import_all_orders():
    """Importa todos os orders da API Anymarket"""
    try:
        logger.info("📥 Iniciando importação completa de orders...")
        
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
            
            # Salvar no banco usando a função EXPANDIDA
            save_orders_to_db_expanded(orders, db)
            
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

def verify_import():
    """Verifica se a importação foi bem-sucedida"""
    try:
        db = SessionLocal()
        
        # Contar total de orders
        total_count = db.query(models.Order).count()
        
        # Buscar alguns exemplos
        sample_orders = db.query(models.Order).limit(5).all()
        
        logger.info(f"📊 Verificação da importação:")
        logger.info(f"   - Total de orders: {total_count}")
        
        if sample_orders:
            logger.info(f"   - Campos expandidos verificados:")
            for order in sample_orders:
                # Verificar se os novos campos estão preenchidos
                address_info = f"Endereço: {order.shipping_address_city}/{order.shipping_address_state}" if order.shipping_address_city else "Sem endereço"
                phone_info = f"Tel: {order.customer_phone}" if order.customer_phone else "Sem tel"
                logger.info(f"     • {order.anymarket_id} - {order.customer_name}")
                logger.info(f"       {address_info} | {phone_info} | R$ {order.total_amount}")
                
                # Verificar se tem dados JSON
                if order.items_data:
                    logger.info(f"       Items: {len(order.items_data)} produtos")
                if order.payments_data:
                    logger.info(f"       Pagamentos: {len(order.payments_data)} formas")
        
        db.close()
        return total_count
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return 0

def main():
    """Função principal do script de migração"""
    print("🔄 MIGRAÇÃO COMPLETA DE ORDERS")
    print("=" * 50)
    print("Este script vai:")
    print("1. Fazer backup dos orders existentes")
    print("2. Resetar a tabela de orders")
    print("3. Importar todos os orders da API novamente")
    print("4. Verificar a importação")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Passo 1: Backup
        print("\n" + "="*30)
        backup_file = backup_existing_orders()
        
        # Passo 2: Reset
        print("\n" + "="*30)
        reset_orders_table()
        
        # Passo 3: Importação
        print("\n" + "="*30)
        total_imported = import_all_orders()
        
        # Passo 4: Verificação
        print("\n" + "="*30)
        total_verified = verify_import()
        
        # Resultado final
        print("\n" + "🎉 MIGRAÇÃO CONCLUÍDA! " + "🎉")
        print("=" * 50)
        if backup_file:
            print(f"💾 Backup salvo em: {backup_file}")
        print(f"📥 Orders importados: {total_imported}")
        print(f"✅ Orders verificados: {total_verified}")
        print("")
        print("💡 Próximos passos:")
        print("   - Testar a API: http://localhost:8000/orders")
        print("   - Verificar documentação: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"💥 Erro durante a migração: {e}")
        print(f"❌ Migração falhou: {e}")

if __name__ == "__main__":
    main()