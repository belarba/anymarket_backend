#!/usr/bin/env python3
"""
Script ULTRA COMPLETO para migrar products com TODOS os campos do modelo atual
Inclui images, skus e characteristics expandidos + todos os campos do models.py
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

def save_products_to_db_ultra_complete_final(products_data, db):
    """
    Salva produtos no banco de dados com TODOS os campos do modelo atual
    Incluindo TODOS os campos images, skus e characteristics expandidos
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
            
            # ===================================================================
            # EXTRAIR E EXPANDIR IMAGES_DATA - TODOS OS CAMPOS DO MODELO
            # ===================================================================
            images = safe_get_value(product_data, "images", [])
            
            # Campos da primeira imagem (ou valores padrão se não houver imagens)
            first_image = images[0] if images else {}
            
            # Image principal
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
            
            # Campos derivados das images
            total_images = len(images)
            has_main_image = any(img.get("main", False) for img in images)
            main_image_url = ""
            
            # Encontrar imagem principal
            for img in images:
                if img.get("main", False):
                    main_image_url = img.get("url", "")
                    break
            
            # Se não encontrou imagem principal, usar a primeira
            if not main_image_url and images:
                main_image_url = images[0].get("url", "")
            
            # ===================================================================
            # EXTRAIR E EXPANDIR SKUS_DATA - TODOS OS CAMPOS DO MODELO
            # ===================================================================
            skus = safe_get_value(product_data, "skus", [])
            
            # Campos do primeiro SKU (ou valores padrão se não houver SKUs)
            first_sku = skus[0] if skus else {}
            
            # SKU principal
            sku_id = str(safe_get_value(first_sku, "id", ""))
            sku_title = safe_get_value(first_sku, "title", "")
            sku_partner_id = safe_get_value(first_sku, "partnerId", "")
            sku_ean = safe_get_value(first_sku, "ean", "")
            sku_price = float(safe_get_value(first_sku, "price", 0))
            sku_amount = int(safe_get_value(first_sku, "amount", 0))
            sku_additional_time = int(safe_get_value(first_sku, "additionalTime", 0))
            sku_stock_local_id = str(safe_get_value(first_sku, "stockLocalId", ""))
            
            # Campos derivados dos SKUs
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
            
            # ===================================================================
            # EXTRAIR E EXPANDIR CHARACTERISTICS_DATA - TODOS OS CAMPOS DO MODELO
            # ===================================================================
            characteristics = safe_get_value(product_data, "characteristics", [])
            
            # Campos da primeira característica (ou valores padrão se não houver características)
            first_characteristic = characteristics[0] if characteristics else {}
            
            # Characteristic principal
            characteristic_index = int(safe_get_value(first_characteristic, "index", 0)) if first_characteristic.get("index") else None
            characteristic_name = safe_get_value(first_characteristic, "name", "")
            characteristic_value = safe_get_value(first_characteristic, "value", "")
            
            # Campos derivados das characteristics
            total_characteristics = len(characteristics)
            has_characteristics = total_characteristics > 0
            
            # ===================================================================
            # MAPEAR TODOS OS CAMPOS PARA O OBJETO PRODUCT - MODELO COMPLETO
            # ===================================================================
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
                
                # ===================================================================
                # IMAGES EXPANDIDAS - TODOS OS CAMPOS DO MODELO
                # ===================================================================
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
                
                # ===================================================================
                # SKUS EXPANDIDOS - TODOS OS CAMPOS DO MODELO
                # ===================================================================
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
                
                # ===================================================================
                # CHARACTERISTICS EXPANDIDAS - TODOS OS CAMPOS DO MODELO
                # ===================================================================
                "characteristic_index": characteristic_index,
                "characteristic_name": characteristic_name,
                "characteristic_value": characteristic_value,
                "total_characteristics": total_characteristics,
                "has_characteristics": has_characteristics,
                
                # ===================================================================
                # CAMPOS LEGADOS (COMPATIBILIDADE)
                # ===================================================================
                "sku": sku_partner_id,  # Campo legacy
                "price": sku_price,     # Campo legacy
                "stock_quantity": sku_amount,  # Campo legacy
                "active": bool(safe_get_value(product_data, "isProductActive", True)),
                
                # ===================================================================
                # DADOS JSON COMPLETOS (para referência completa)
                # ===================================================================
                "characteristics": characteristics,
                "images": images,
                "skus": skus,
                
                # Status de sincronização
                "sync_status": "synced",
                "last_sync_date": datetime.now(),
            }
            
            if existing_product:
                # Atualizar produto existente
                for field, value in product_fields.items():
                    if field != "anymarket_id":
                        setattr(existing_product, field, value)
                existing_product.updated_at = datetime.now()
                logger.info(f"📦 Product atualizado: {anymarket_id} - Images: {total_images}, SKUs: {total_skus}, Chars: {total_characteristics}")
            else:
                # Criar novo produto
                new_product = models.Product(**product_fields)
                db.add(new_product)
                logger.info(f"✨ Product criado: {anymarket_id} - Images: {total_images}, SKUs: {total_skus}, Chars: {total_characteristics}")
                
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Erro ao processar product {product_data.get('id')}: {e}")
            continue
    
    db.commit()

def reset_products_table():
    """Reseta apenas a tabela de products"""
    try:
        logger.info("🗑️  Resetando tabela 'products'...")
        
        # Drop e recriar tabela
        models.Product.__table__.drop(bind=engine, checkfirst=True)
        models.Product.__table__.create(bind=engine)
        
        logger.info("✅ Tabela 'products' resetada com estrutura ULTRA COMPLETA FINAL")
        
    except Exception as e:
        logger.error(f"❌ Erro ao resetar tabela: {e}")
        raise

def import_all_products():
    """Importa todos os produtos da API Anymarket com estrutura ultra completa final"""
    try:
        logger.info("📥 Iniciando importação ULTRA COMPLETA FINAL de products...")
        
        # Instanciar cliente e sessão do banco
        client = AnymarketClient()
        db = SessionLocal()
        
        offset = 0
        limit = 50
        total_imported = 0
        
        while True:
            logger.info(f"🔍 Buscando products: offset {offset}, limit {limit}")
            
            # Buscar produtos da API
            products_response = client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                logger.info("📭 Nenhum produto encontrado. Importação finalizada.")
                break
            
            logger.info(f"📦 Processando {len(products)} produtos...")
            
            # Salvar no banco usando a função ULTRA COMPLETA FINAL
            save_products_to_db_ultra_complete_final(products, db)
            
            total_imported += len(products)
            offset += limit
            
            logger.info(f"✅ Total importado até agora: {total_imported}")
            
            # Se retornou menos que o limite, não há mais produtos
            if len(products) < limit:
                break
            
            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.5)
        
        logger.info(f"🎉 Importação ULTRA COMPLETA FINAL concluída! Total: {total_imported} produtos")
        
        db.close()
        return total_imported
        
    except Exception as e:
        logger.error(f"❌ Erro na importação: {e}")
        raise

def verify_ultra_complete_final_import():
    """Verifica se a importação com estrutura ultra completa final funcionou"""
    try:
        db = SessionLocal()
        
        # Contar total de produtos
        total_count = db.query(models.Product).count()
        
        # Buscar alguns exemplos
        sample_products = db.query(models.Product).limit(2).all()
        
        logger.info(f"📊 Verificação da importação ULTRA COMPLETA FINAL:")
        logger.info(f"   - Total de produtos: {total_count}")
        
        if sample_products:
            logger.info(f"   - Estrutura ULTRA COMPLETA FINAL verificada:")
            for product in sample_products:
                logger.info(f"     • Product {product.anymarket_id}")
                
                # Verificar campos básicos
                logger.info(f"       Título: {product.title[:50]}...")
                logger.info(f"       Marca: {product.brand_name}")
                logger.info(f"       Categoria: {product.category_name}")
                
                # Verificar IMAGES expandidas
                images_info = []
                if product.image_url:
                    images_info.append(f"URL: {product.image_url[:50]}...")
                if product.image_main:
                    images_info.append("Principal")
                if product.image_status:
                    images_info.append(f"Status: {product.image_status}")
                if product.image_standard_width and product.image_standard_height:
                    images_info.append(f"Tamanho: {product.image_standard_width}x{product.image_standard_height}")
                
                if images_info:
                    logger.info(f"       Images: {' | '.join(images_info)}")
                
                # Verificar SKUS expandidos
                skus_info = []
                if product.sku_partner_id:
                    skus_info.append(f"SKU: {product.sku_partner_id}")
                if product.sku_price:
                    skus_info.append(f"Preço: R$ {product.sku_price}")
                if product.sku_amount:
                    skus_info.append(f"Estoque: {product.sku_amount}")
                if product.sku_ean:
                    skus_info.append(f"EAN: {product.sku_ean}")
                
                if skus_info:
                    logger.info(f"       SKUs: {' | '.join(skus_info)}")
                
                # Verificar CHARACTERISTICS expandidas
                chars_info = []
                if product.characteristic_name:
                    chars_info.append(f"Nome: {product.characteristic_name}")
                if product.characteristic_value:
                    chars_info.append(f"Valor: {product.characteristic_value}")
                
                if chars_info:
                    logger.info(f"       Characteristics: {' | '.join(chars_info)}")
                
                # Verificar campos derivados
                logger.info(f"       Totais: {product.total_images} imgs, {product.total_skus} SKUs, {product.total_characteristics} chars")
                
                # Verificar faixa de preços
                if product.min_price and product.max_price:
                    logger.info(f"       Preços: R$ {product.min_price} - R$ {product.max_price} (Média: R$ {product.avg_price})")
                
                # Verificar estoque
                logger.info(f"       Estoque total: {product.total_stock} | Tem estoque: {product.has_stock}")
        
        db.close()
        return total_count
        
    except Exception as e:
        logger.error(f"❌ Erro na verificação: {e}")
        return 0

def show_final_products_table_structure():
    """Mostra a estrutura final da tabela products"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        
        if 'products' not in inspector.get_table_names():
            logger.error("❌ Tabela 'products' não encontrada!")
            return
        
        columns = inspector.get_columns('products')
        
        logger.info(f"📋 ESTRUTURA FINAL DA TABELA PRODUCTS:")
        logger.info(f"   Total de colunas: {len(columns)}")
        
        # Agrupar colunas por categoria
        categories = {
            "Básicos": ["id", "anymarket_id", "title", "description", "model"],
            "Category": [col for col in [c['name'] for c in columns] if col.startswith('category_')],
            "Brand": [col for col in [c['name'] for c in columns] if col.startswith('brand_')],
            "NBM": [col for col in [c['name'] for c in columns] if col.startswith('nbm_')],
            "Origin": [col for col in [c['name'] for c in columns] if col.startswith('origin_')],
            "Images": [col for col in [c['name'] for c in columns] if col.startswith('image_') or col.startswith('total_images') or col.startswith('has_main_image') or col.startswith('main_image_url')],
            "SKUs": [col for col in [c['name'] for c in columns] if col.startswith('sku_') or col.startswith('total_skus') or col.startswith('min_price') or col.startswith('max_price') or col.startswith('avg_price') or col.startswith('has_stock') or col.startswith('total_stock')],
            "Characteristics": [col for col in [c['name'] for c in columns] if col.startswith('characteristic_') or col.startswith('total_characteristics') or col.startswith('has_characteristics')],
            "Dimensões": ["height", "width", "length", "weight"],
            "Garantia": ["warranty_time", "warranty_text"],
            "Status": ["active", "is_product_active", "has_variations"],
            "JSON": ["characteristics", "images", "skus"]
        }
        
        for category, fields in categories.items():
            existing_fields = [f for f in fields if f in [c['name'] for c in columns]]
            if existing_fields:
                logger.info(f"   {category}: {len(existing_fields)} campos")
                
    except Exception as e:
        logger.error(f"❌ Erro ao verificar estrutura: {e}")

def main():
    """Função principal do script de migração ultra completa final"""
    print("🔄 MIGRAÇÃO ULTRA COMPLETA FINAL - PRODUCTS")
    print("=" * 60)
    print("Este script vai:")
    print("1. Resetar a tabela products com estrutura ULTRA COMPLETA")
    print("2. Importar todos os produtos com TODOS os campos do modelo atual")
    print("3. Incluir TODOS os campos images, skus e characteristics expandidos")
    print("4. Estrutura final: ~75 campos expandidos")
    print("5. Verificar se tudo está funcionando corretamente")
    print("")
    print("🔍 Campos que serão criados:")
    print("   ✅ Images expandidas: image_url, image_main, image_status, etc.")
    print("   ✅ SKUs expandidos: sku_partner_id, sku_price, sku_amount, etc.")
    print("   ✅ Characteristics expandidas: characteristic_name, characteristic_value, etc.")
    print("   ✅ Todos os objetos aninhados viram colunas individuais")
    print("   ✅ Arrays complexos mantidos como JSON para referência")
    print("")
    
    confirm = input("Deseja continuar? (sim/nao): ").strip().lower()
    
    if confirm not in ['sim', 's', 'yes', 'y']:
        print("❌ Operação cancelada")
        return
    
    try:
        # Passo 1: Reset da tabela
        print("\n" + "="*40)
        reset_products_table()
        
        # Passo 1.5: Mostrar estrutura
        print("\n" + "="*40)
        show_final_products_table_structure()
        
        # Passo 2: Importação
        print("\n" + "="*40)
        total_imported = import_all_products()
        
        # Passo 3: Verificação
        print("\n" + "="*40)
        total_verified = verify_ultra_complete_final_import()
        
        # Resultado final
        print("\n" + "🎊 MIGRAÇÃO ULTRA COMPLETA FINAL CONCLUÍDA! " + "🎊")
        print("=" * 60)
        print(f"📥 Products importados: {total_imported}")
        print(f"✅ Products verificados: {total_verified}")
        print("")
        print("💡 Estrutura ULTRA COMPLETA FINAL implementada:")
        print("   ✅ ~75 campos expandidos por produto")
        print("   ✅ Images: url, main, status, width, height, etc.")
        print("   ✅ SKUs: partner_id, price, amount, ean, stock_local_id, etc.")
        print("   ✅ Characteristics: name, value, index, etc.")
        print("   ✅ Todos os objetos aninhados → colunas individuais")
        print("   ✅ Arrays complexos mantidos como JSON")
        print("   ✅ Campos derivados calculados (totais, preços, estoque)")
        print("")
        print("🚀 Novos endpoints disponíveis:")
        print("   - /products/sku/SKU_PARTNER_ID")
        print("   - /products/ean/EAN_CODE")
        print("   - /products/price-range?min=100&max=500")
        print("   - /products/with-stock")
        print("   - /products/with-images")
        print("   - /products/characteristic/NOME/VALOR")
        print("   - /stats/products/ultra-detailed")
        print("")
        print("💡 Próximos passos:")
        print("   1. Atualizar main.py com novos endpoints")
        print("   2. Iniciar API: python -m app.main")
        print("   3. Testar: http://localhost:8000/products")
        print("   4. Ver exemplo: http://localhost:8000/examples/product-ultra-complete")
        print("   5. Documentação: http://localhost:8000/docs")
        print("")
        print("🎯 Agora você pode fazer consultas SQL diretas em todos os campos!")
        
    except Exception as e:
        logger.error(f"💥 Erro durante a migração: {e}")
        print(f"❌ Migração falhou: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()