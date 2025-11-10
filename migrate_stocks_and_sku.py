
import os
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent))

from app.database import engine, SessionLocal
from app import models
from app.anymarket_client import AnymarketClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_new_tables():
    """Cria as novas tabelas stocks e sku_marketplaces"""
    try:
        logger.info("🔨 Criando tabelas stocks e sku_marketplaces...")
        
        # Criar apenas as novas tabelas
        models.Stock.__table__.create(bind=engine, checkfirst=True)
        models.SkuMarketplace.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("✅ Tabelas criadas com sucesso!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar tabelas: {e}")
        return False

def import_all_stocks(client, db):
    """Importa todos os stocks"""
    try:
        logger.info("📊 Iniciando importação de stocks...")
        
        offset = 0
        limit = 50
        total = 0
        
        while True:
            logger.info(f"🔍 Buscando stocks: offset {offset}")
            
            stocks_response = client.get_stocks(limit=limit, offset=offset)
            stocks = stocks_response.get("content", [])
            
            if not stocks:
                break
            
            # Processar stocks (função simplificada do daily_update.py)
            for stock_data in stocks:
                try:
                    sku = stock_data.get("stockKeepingUnit", {})
                    stock_local = stock_data.get("stockLocal", {})
                    
                    sku_id = str(sku.get("id", ""))
                    stock_local_id = str(stock_local.get("id", ""))
                    sku_stock_key = f"{sku_id}_{stock_local_id}"
                    
                    existing = db.query(models.Stock).filter(
                        models.Stock.sku_stock_key == sku_stock_key
                    ).first()
                    
                    if not existing:
                        new_stock = models.Stock(
                            sku_id=sku_id,
                            sku_title=sku.get("title", ""),
                            sku_partner_id=sku.get("partnerId", ""),
                            stock_local_id=stock_local_id,
                            stock_local_name=stock_local.get("name", ""),
                            amount=int(stock_data.get("amount", 0)),
                            available_amount=int(stock_data.get("availableAmount", 0)),
                            price=float(stock_data.get("price", 0)),
                            active=bool(stock_data.get("active", True)),
                            sku_stock_key=sku_stock_key,
                            stock_keeping_unit_data=sku,
                            stock_local_data=stock_local,
                            sync_status="synced",
                            last_sync_date=datetime.now()
                        )
                        db.add(new_stock)
                        total += 1
                        
                except Exception as e:
                    logger.error(f"Erro ao processar stock: {e}")
                    continue
            
            db.commit()
            logger.info(f"✅ {len(stocks)} stocks processados. Total: {total}")
            
            offset += limit
            
            if len(stocks) < limit:
                break
            
            time.sleep(0.5)
        
        logger.info(f"🎉 Importação de stocks concluída! Total: {total}")
        return total
        
    except Exception as e:
        logger.error(f"❌ Erro na importação de stocks: {e}")
        return 0

def import_all_sku_marketplaces(client, db):
    """Importa todos os SKU marketplaces"""
    try:
        logger.info("🏪 Iniciando importação de SKU marketplaces...")
        
        offset = 0
        limit = 50
        total = 0
        
        while True:
            logger.info(f"🔍 Buscando SKU marketplaces: offset {offset}")
            
            sku_mps = client.get_sku_marketplaces(limit=limit, offset=offset)
            
            if not sku_mps:
                break
            
            # Processar SKU marketplaces
            for sku_mp_data in sku_mps:
                try:
                    anymarket_id = str(sku_mp_data.get("id", ""))
                    marketplace = sku_mp_data.get("marketPlace", "")
                    id_in_marketplace = sku_mp_data.get("idInMarketplace", "")
                    sku_marketplace_key = f"{anymarket_id}_{marketplace}_{id_in_marketplace}"
                    
                    existing = db.query(models.SkuMarketplace).filter(
                        models.SkuMarketplace.sku_marketplace_key == sku_marketplace_key
                    ).first()
                    
                    if not existing:
                        fields = sku_mp_data.get("fields", {})
                        
                        new_sku_mp = models.SkuMarketplace(
                            anymarket_id=anymarket_id,
                            marketplace=marketplace,
                            id_in_marketplace=id_in_marketplace,
                            publication_status=sku_mp_data.get("publicationStatus", ""),
                            price=float(sku_mp_data.get("price", 0)),
                            field_title=fields.get("title", ""),
                            field_ean=fields.get("EAN", ""),
                            field_condition=fields.get("condition", ""),
                            sku_marketplace_key=sku_marketplace_key,
                            fields_data=fields,
                            attributes_data=sku_mp_data.get("attributes", {}),
                            warnings=sku_mp_data.get("warnings", []),
                            sync_status="synced",
                            last_sync_date=datetime.now()
                        )
                        db.add(new_sku_mp)
                        total += 1
                        
                except Exception as e:
                    logger.error(f"Erro ao processar SKU marketplace: {e}")
                    continue
            
            db.commit()
            logger.info(f"✅ {len(sku_mps)} SKU marketplaces processados. Total: {total}")
            
            offset += limit
            
            if len(sku_mps) < limit:
                break
            
            time.sleep(0.5)
        
        logger.info(f"🎉 Importação de SKU marketplaces concluída! Total: {total}")
        return total
        
    except Exception as e:
        logger.error(f"❌ Erro na importação de SKU marketplaces: {e}")
        return 0

def main():
    print("🔄 MIGRAÇÃO - STOCKS E SKU MARKETPLACES")
    print("=" * 60)
    print("Este script vai:")
    print("1. Criar as tabelas stocks e sku_marketplaces")
    print("2. Importar todos os stocks")
    print("3. Importar todos os SKU marketplaces")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Criar tabelas
        print("\n" + "="*40)
        if not create_new_tables():
            print("❌ Falha ao criar tabelas")
            return
        
        # Instanciar cliente e DB
        client = AnymarketClient()
        db = SessionLocal()
        
        # Importar stocks
        print("\n" + "="*40)
        stocks_imported = import_all_stocks(client, db)
        
        # Importar SKU marketplaces
        print("\n" + "="*40)
        sku_mp_imported = import_all_sku_marketplaces(client, db)
        
        # Resultado final
        print("\n" + "🎉 MIGRAÇÃO CONCLUÍDA! " + "🎉")
        print("=" * 60)
        print(f"📊 Stocks importados: {stocks_imported}")
        print(f"🏪 SKU Marketplaces importados: {sku_mp_imported}")
        print("")
        print("💡 Próximos passos:")
        print("   1. Adicionar os novos modelos ao app/models.py")
        print("   2. Adicionar as funções ao app/anymarket_client.py")
        print("   3. Usar o daily_update_v2.py para atualizações diárias")
        print("   4. Criar endpoints na API para consultar os dados")
        
        db.close()
        
    except Exception as e:
        logger.error(f"💥 Erro: {e}")
        print(f"❌ Migração falhou: {e}")

if __name__ == "__main__":
    main()