#!/usr/bin/env python3
"""
Script completo para migrar products com TODOS os campos expandidos
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

def save_products_to_db_complete(products_data, db):
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
                logger.info(f"📦 Produto atualizado: {anymarket_id} - {product_fields['title'][:30]}...")
            else:
                # Criar novo produto
                new_product = models.Product(**product_fields)
                db.add(new_product)
                logger.info(f"✨ Produto criado: {anymarket_id} - {product_fields['title'][:30]}...")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar produto {product_data.get('id')}: {e}")
            continue
    
    db.commit()

def reset_products_table():
    """Reseta apenas a tabela de products"""
    try:
        logger.info("🗑️  Resetando tabela 'products'...")
        
        # Drop e recriar tabela
        models.Product.__table__.drop(bind=engine, checkfirst=True)
        models.Product.__table__.create(bind=engine)
        
        logger.info("✅ Tabela 'products' resetada com estrutura COMPLETA")
        
    except Exception as e:
        logger.error(f"❌ Erro ao resetar tabela: {e}")
        raise

def import_all_products():
    """Importa todos os produtos da API Anymarket com estrutura completa"""
    try:
        logger.info("📥 Iniciando importação COMPLETA de produtos...")
        
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
            
            # Salvar no banco usando a função COMPLETA
            save_products_to_db_complete(products, db)
            
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

def verify_complete_import():
    """Verifica se a importação com estrutura completa funcionou"""
    try:
        db = SessionLocal()
        
        # Contar total de produtos
        total_count = db.query(models.Product).count()
        
        # Buscar alguns exemplos
        sample_products = db.query(models.Product).limit(3).all()
        
        logger.info(f"📊 Verificação da importação COMPLETA:")
        logger.info(f"   - Total de produtos: {total_count}")
        
        if sample_products:
            logger.info(f"   - Estrutura COMPLETA verificada:")
            for product in sample_products:
                logger.info(f"     • Produto {product.anymarket_id}")
                
                # Verificar campos básicos
                logger.info(f"       Título: {product.title[:50]}...")
                logger.info(f"       Preço: R$ {product.price}")
                
                # Verificar campos expandidos de brand
                if product.brand_name:
                    brand_info = f"Marca: {product.brand_name}"
                    if product.brand_id:
                        brand_info += f" (ID: {product.brand_id})"
                    logger.info(f"       {brand_info}")
                
                # Verificar campos expandidos de category
                if product.category_name:
                    category_info = f"Categoria: {product.category_name}"
                    if product.category_path:
                        category_info += f" ({product.category_path})"
                    logger.info(f"       {category_info}")
                
                # Verificar dimensões expandidas
                if product.height or product.width or product.length:
                    dimensions = f"Dimensões: {product.height or 0}x{product.width or 0}x{product.length or 0}cm"
                    if product.weight:
                        dimensions += f", {product.weight}kg"
                    logger.info(f"       {dimensions}")
                
                # Verificar campos derivados
                logger.info(f"       SKUs: {product.total_skus}, Imagens: {product.total_images}")
                logger.info(f"       Estoque total: {product.total_stock}")
                
                if product.min_price and product.max_price:
                    logger.info(f"       Faixa de preço: R$ {product.min_price} - R$ {product.max_price}")
                
                # Verificar dados JSON
                json_fields = [
                    ("Características", product.characteristics),
                    ("Imagens", product.images),
                    ("SKUs", product.skus)
                ]
                for field_name, field_data in json_fields:
                    if field_data:
                        logger.info(f"       {field_name} JSON: {len(field_data)} registros")
        
        db.close()
        return total_count
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return 0

def show_products_table_structure():
    """Mostra a estrutura da tabela products"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        if 'products' not in inspector.get_table_names():
            logger.error("❌ Tabela 'products' não encontrada!")
            return
        
        columns = inspector.get_columns('products')
        
        logger.info(f"📋 ESTRUTURA DA TABELA PRODUCTS:")
        logger.info(f"   Total de colunas: {len(columns)}")
        
        # Agrupar colunas por categoria
        categories = {
            "Básicos": ["id", "anymarket_id", "title", "description", "model"],
            "Category": [col for col in [c['name'] for c in columns] if col.startswith('category_')],
            "Brand": [col for col in [c['name'] for c in columns] if col.startswith('brand_')],
            "NBM": [col for col in [c['name'] for c in columns] if col.startswith('nbm_')],
            "Origin": [col for col in [c['name'] for c in columns] if col.startswith('origin_')],
            "Dimensões": ["height", "width", "length", "weight"],
            "Garantia": ["warranty_time", "warranty_text"],
            "Preços": ["price", "min_price", "max_price", "price_factor"],
            "Status": ["active", "is_product_active", "has_variations"],
            "Derivados": ["total_skus", "total_images", "total_stock", "main_image_url"],
            "JSON": ["characteristics", "images", "skus"]
        }
        
        for category, fields in categories.items():
            existing_fields = [f for f in fields if f in [c['name'] for c in columns]]
            if existing_fields:
                logger.info(f"   {category}: {len(existing_fields)} campos")
                
    except Exception as e:
        logger.error(f"❌ Erro ao verificar estrutura: {e}")

def main():
    """Função principal do script de migração completa"""
    print("🔄 MIGRAÇÃO COMPLETA DE PRODUCTS - ANYMARKET")
    print("=" * 50)
    print("Este script vai:")
    print("1. Resetar a tabela products com estrutura COMPLETA")
    print("2. Importar todos os produtos com TODOS os campos expandidos")
    print("3. Cada objeto aninhado vira colunas individuais")
    print("4. Calcular campos derivados (totais, preços, etc.)")
    print("5. Verificar se a estrutura está correta")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Passo 1: Reset da tabela
        print("\n" + "="*30)
        reset_products_table()
        
        # Passo 1.5: Mostrar estrutura
        print("\n" + "="*30)
        show_products_table_structure()
        
        # Passo 2: Importação
        print("\n" + "="*30)
        total_imported = import_all_products()
        
        # Passo 3: Verificação
        print("\n" + "="*30)
        total_verified = verify_complete_import()
        
        # Resultado final
        print("\n" + "🎉 MIGRAÇÃO COMPLETA DE PRODUCTS CONCLUÍDA! " + "🎉")
        print("=" * 50)
        print(f"📥 Produtos importados: {total_imported}")
        print(f"✅ Produtos verificados: {total_verified}")
        print("")
        print("💡 Estrutura COMPLETA implementada:")
        print("   ✅ Objetos aninhados viram colunas individuais")
        print("   ✅ category.* → category_*")
        print("   ✅ brand.* → brand_*")
        print("   ✅ nbm.* → nbm_*")
        print("   ✅ origin.* → origin_*")
        print("   ✅ Campos derivados calculados (totais, preços)")
        print("   ✅ Arrays complexos mantidos como JSON")
        print("")
        print("💡 Próximos passos:")
        print("   - Testar API: python -m app.main")
        print("   - Ver produtos: http://localhost:8000/products")
        print("   - Produtos completos: http://localhost:8000/products/full")
        print("   - Busca avançada: http://localhost:8000/products/search/termo")
        print("   - Por marca: http://localhost:8000/products/brand/marca")
        print("   - Por categoria: http://localhost:8000/products/category/categoria")
        print("   - Documentação: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"💥 Erro durante a migração: {e}")
        print(f"❌ Migração falhou: {e}")

if __name__ == "__main__":
    main()