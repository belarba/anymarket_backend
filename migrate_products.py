#!/usr/bin/env python3
"""
Script completo para migrar products:
1. Backup dos dados existentes (opcional)
2. Reset da tabela products
3. Reimportação completa via API com campos expandidos
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

def save_products_to_db_expanded(products_data, db):
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

def backup_existing_products():
    """Faz backup dos produtos existentes em JSON"""
    try:
        db = SessionLocal()
        
        logger.info("💾 Fazendo backup dos produtos existentes...")
        
        # Buscar todos os produtos
        products = db.query(models.Product).all()
        
        if not products:
            logger.info("📭 Nenhum produto encontrado para backup")
            db.close()
            return None
        
        # Converter para dict
        backup_data = []
        for product in products:
            product_dict = {
                "id": product.id,
                "anymarket_id": product.anymarket_id,
                "title": product.title,
                "sku": product.sku,
                "brand_name": product.brand_name,
                "category_name": product.category_name,
                "price": product.price,
                "stock_quantity": product.stock_quantity,
                "active": product.active,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None,
            }
            backup_data.append(product_dict)
        
        # Salvar backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"products_backup_{timestamp}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Backup salvo: {backup_filename} ({len(backup_data)} produtos)")
        
        db.close()
        return backup_filename
        
    except Exception as e:
        logger.error(f"❌ Erro no backup: {e}")
        return None

def reset_products_table():
    """Reseta apenas a tabela de produtos"""
    try:
        logger.info("🗑️  Resetando tabela 'products'...")
        
        # Drop e recriar tabela
        models.Product.__table__.drop(bind=engine, checkfirst=True)
        models.Product.__table__.create(bind=engine)
        
        logger.info("✅ Tabela 'products' resetada")
        
    except Exception as e:
        logger.error(f"❌ Erro ao resetar tabela: {e}")
        raise

def import_all_products():
    """Importa todos os produtos da API Anymarket"""
    try:
        logger.info("📥 Iniciando importação EXPANDIDA de produtos...")
        
        # Instanciar cliente e sessão do banco
        client = AnymarketClient()
        db = SessionLocal()
        
        offset = 0
        limit = 50
        total_imported = 0
        
        while True:
            logger.info(f"🔍 Buscando produtos: offset {offset}, limit {limit}")
            
            # Buscar produtos da API
            products_response = client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                logger.info("📭 Nenhum produto encontrado. Importação finalizada.")
                break
            
            logger.info(f"📦 Processando {len(products)} produtos...")
            
            # Salvar no banco
            save_products_to_db_expanded(products, db)
            
            total_imported += len(products)
            offset += limit
            
            logger.info(f"✅ Total importado até agora: {total_imported}")
            
            # Se retornou menos que o limite, não há mais produtos
            if len(products) < limit:
                break
            
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
        
        logger.info(f"🎉 Importação concluída! Total: {total_imported} produtos")
        
        db.close()
        return total_imported
        
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        raise

def verify_import():
    """Verifica se a importação foi bem-sucedida"""
    try:
        db = SessionLocal()
        
        # Contar total de produtos
        total_count = db.query(models.Product).count()
        
        # Buscar alguns exemplos
        sample_products = db.query(models.Product).limit(5).all()
        
        logger.info(f"📊 Verificação da importação:")
        logger.info(f"   - Total de produtos: {total_count}")
        
        if sample_products:
            logger.info(f"   - Campos expandidos verificados:")
            for product in sample_products:
                # Verificar se os novos campos estão preenchidos
                brand_info = f"Marca: {product.brand_name}" if product.brand_name else "Sem marca"
                category_info = f"Cat: {product.category_name}" if product.category_name else "Sem categoria"
                dimensions = f"{product.height}x{product.width}x{product.length}" if product.height else "Sem dimensões"
                
                logger.info(f"     • {product.anymarket_id} - {product.title}")
                logger.info(f"       {brand_info} | {category_info} | R$ {product.price}")
                logger.info(f"       SKU: {product.sku} | Estoque: {product.stock_quantity}")
                logger.info(f"       Dimensões: {dimensions}")
                
                # Verificar dados JSON
                if product.characteristics:
                    logger.info(f"       Características: {len(product.characteristics)} itens")
                if product.images:
                    logger.info(f"       Imagens: {len(product.images)} fotos")
                if product.skus:
                    logger.info(f"       SKUs: {len(product.skus)} variações")
        
        db.close()
        return total_count
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return 0

def main():
    """Função principal do script de migração"""
    print("🔄 MIGRAÇÃO EXPANDIDA DE PRODUTOS")
    print("=" * 50)
    print("Este script vai:")
    print("1. Fazer backup dos produtos existentes")
    print("2. Resetar a tabela de produtos")
    print("3. Importar todos os produtos da API com campos expandidos")
    print("4. Verificar a importação")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Passo 1: Backup
        print("\n" + "="*30)
        backup_file = backup_existing_products()
        
        # Passo 2: Reset
        print("\n" + "="*30)
        reset_products_table()
        
        # Passo 3: Importação
        print("\n" + "="*30)
        total_imported = import_all_products()
        
        # Passo 4: Verificação
        print("\n" + "="*30)
        total_verified = verify_import()
        
        # Resultado final
        print("\n" + "🎉 MIGRAÇÃO DE PRODUTOS CONCLUÍDA! " + "🎉")
        print("=" * 50)
        if backup_file:
            print(f"💾 Backup salvo em: {backup_file}")
        print(f"📥 Produtos importados: {total_imported}")
        print(f"✅ Produtos verificados: {total_verified}")
        print("")
        print("💡 Próximos passos:")
        print("   - Testar a API: http://localhost:8000/products")
        print("   - Ver produtos completos: http://localhost:8000/products/full")
        print("   - Verificar documentação: http://localhost:8000/docs")
        print("   - Buscar produto: http://localhost:8000/products/search/termo")
        
    except Exception as e:
        logger.error(f"💥 Erro durante a migração: {e}")
        print(f"❌ Migração falhou: {e}")

if __name__ == "__main__":
    main()