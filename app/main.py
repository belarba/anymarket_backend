# ADICIONAR ESTAS FUNÇÕES E ENDPOINTS NO MAIN.PY EXISTENTE

# Função completa de salvamento de products com campos expandidos
def save_products_to_db_ultra_complete(products_data: List[Dict], db: Session):
    """
    Salva produtos no banco de dados com TODOS os campos expandidos
    Incluindo images, skus e characteristics expandidos em colunas individuais
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
            # EXTRAIR E EXPANDIR IMAGES_DATA
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
            # EXTRAIR E EXPANDIR SKUS_DATA
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
            # EXTRAIR E EXPANDIR CHARACTERISTICS_DATA
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
            # MAPEAR TODOS OS CAMPOS PARA O OBJETO PRODUCT
            # ===================================================================
            product_fields = {
                # Campos básicos
                "anymarket_id": anymarket_id,
                "title": safe_get_value(product_data, "title", ""),
                "description": safe_get_value(product_data, "description", ""),
                "external_id_product": safe_get_value(product_data, "externalIdProduct", ""),
                
                # Category expandida
                "category_id": str(safe_get_value(category, "id", "")),
                "category_name": safe_get_value(category, "name", ""),
                "category_path": safe_get_value(category, "path", ""),
                
                # Brand expandida
                "brand_id": str(safe_get_value(brand, "id", "")),
                "brand_name": safe_get_value(brand, "name", ""),
                "brand_reduced_name": safe_get_value(brand, "reducedName", ""),
                "brand_partner_id": safe_get_value(brand, "partnerId", ""),
                
                # NBM expandido
                "nbm_id": safe_get_value(nbm, "id", ""),
                "nbm_description": safe_get_value(nbm, "description", ""),
                
                # Origin expandido
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

# =============================================================================
# ATUALIZAR ENDPOINT DE SINCRONIZAÇÃO DE PRODUTOS
# =============================================================================

@app.post("/sync/products")
def sync_products(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Sincroniza produtos da API Anymarket com TODOS os campos expandidos"""
    def sync_task():
        offset = 0
        limit = 50
        total_products = 0
        
        logger.info("🚀 Iniciando sincronização ULTRA COMPLETA de produtos...")
        
        while True:
            logger.info(f"🔍 Buscando produtos: offset {offset}, limit {limit}")
            products_response = anymarket_client.get_products(limit=limit, offset=offset)
            products = products_response.get("content", [])
            
            if not products:
                break
            
            save_products_to_db_ultra_complete(products, db)
            total_products += len(products)
            offset += limit
            
            logger.info(f"📊 Total de produtos processados: {total_products}")
            
            if len(products) < limit:
                break
        
        logger.info(f"🎉 Sincronização ULTRA COMPLETA de produtos concluída. Total: {total_products}")
    
    background_tasks.add_task(sync_task)
    return {"message": "Sincronização ULTRA COMPLETA de produtos iniciada (com images, skus e characteristics expandidos)"}

# =============================================================================
# NOVOS ENDPOINTS ESPECIALIZADOS PARA PRODUCTS COM CAMPOS EXPANDIDOS
# =============================================================================

@app.get("/products/sku/{sku_partner_id}")
def get_products_by_sku_partner_id(sku_partner_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos por SKU Partner ID (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.sku_partner_id == sku_partner_id
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/ean/{ean_code}")
def get_products_by_ean(ean_code: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos por código EAN (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.sku_ean == ean_code
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/price-range")
def get_products_by_price_range(
    min_price: float = Query(..., description="Preço mínimo"),
    max_price: float = Query(..., description="Preço máximo"),
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Retorna produtos em uma faixa de preços (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.sku_price.between(min_price, max_price)
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/with-stock")
def get_products_with_stock(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos com estoque disponível (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.has_stock == True
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/with-images")
def get_products_with_images(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos que têm imagens (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.has_main_image == True
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/image-status/{status}")
def get_products_by_image_status(status: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos por status da imagem (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.image_status == status
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/characteristic/{name}/{value}")
def get_products_by_characteristic(name: str, value: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos por característica específica (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.characteristic_name.ilike(f"%{name}%"),
        models.Product.characteristic_value.ilike(f"%{value}%")
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/stock-location/{stock_local_id}")
def get_products_by_stock_location(stock_local_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos de um local de estoque específico (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.sku_stock_local_id == stock_local_id
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/brand/{brand_name}")
def get_products_by_brand_name(brand_name: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos por nome da marca (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.brand_name.ilike(f"%{brand_name}%")
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/category/{category_name}")
def get_products_by_category_name(category_name: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos por nome da categoria (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.category_name.ilike(f"%{category_name}%")
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/variations")
def get_products_with_variations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos que têm variações (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.has_variations == True
    ).offset(skip).limit(limit).all()
    return products

@app.get("/products/multiple-skus")
def get_products_with_multiple_skus(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retorna produtos com múltiplos SKUs (campo expandido)"""
    products = db.query(models.Product).filter(
        models.Product.total_skus > 1
    ).offset(skip).limit(limit).all()
    return products

# =============================================================================
# ENDPOINT DE ESTATÍSTICAS ULTRA DETALHADAS PARA PRODUCTS
# =============================================================================

@app.get("/stats/products/ultra-detailed")
def get_products_statistics_ultra_detailed(db: Session = Depends(get_db)):
    """Estatísticas ultra detalhadas incluindo images, skus e characteristics expandidos"""
    from sqlalchemy import func
    
    # Estatísticas básicas
    total_products = db.query(models.Product).count()
    products_with_images = db.query(models.Product).filter(models.Product.has_main_image == True).count()
    products_with_stock = db.query(models.Product).filter(models.Product.has_stock == True).count()
    products_with_characteristics = db.query(models.Product).filter(models.Product.has_characteristics == True).count()
    
    # Estatísticas de images
    total_images = db.query(func.sum(models.Product.total_images)).scalar() or 0
    avg_images_per_product = db.query(func.avg(models.Product.total_images)).scalar() or 0
    
    # Estatísticas de SKUs
    total_skus = db.query(func.sum(models.Product.total_skus)).scalar() or 0
    avg_skus_per_product = db.query(func.avg(models.Product.total_skus)).scalar() or 0
    total_stock = db.query(func.sum(models.Product.total_stock)).scalar() or 0
    
    # Estatísticas de characteristics
    total_characteristics = db.query(func.sum(models.Product.total_characteristics)).scalar() or 0
    avg_characteristics_per_product = db.query(func.avg(models.Product.total_characteristics)).scalar() or 0
    
    # Estatísticas de preços
    min_price = db.query(func.min(models.Product.sku_price)).scalar() or 0
    max_price = db.query(func.max(models.Product.sku_price)).scalar() or 0
    avg_price = db.query(func.avg(models.Product.sku_price)).scalar() or 0
    
    # Top marcas
    top_brands = db.query(
        models.Product.brand_name,
        func.count(models.Product.id).label('count')
    ).filter(
        models.Product.brand_name.isnot(None),
        models.Product.brand_name != ""
    ).group_by(
        models.Product.brand_name
    ).order_by(func.count(models.Product.id).desc()).limit(10).all()
    
    # Top categorias
    top_categories = db.query(
        models.Product.category_name,
        func.count(models.Product.id).label('count')
    ).filter(
        models.Product.category_name.isnot(None),
        models.Product.category_name != ""
    ).group_by(
        models.Product.category_name
    ).order_by(func.count(models.Product.id).desc()).limit(10).all()
    
    # Status das imagens
    image_statuses = db.query(
        models.Product.image_status,
        func.count(models.Product.id).label('count')
    ).filter(
        models.Product.image_status.isnot(None),
        models.Product.image_status != ""
    ).group_by(
        models.Product.image_status
    ).order_by(func.count(models.Product.id).desc()).all()
    
    # Locais de estoque
    stock_locations = db.query(
        models.Product.sku_stock_local_id,
        func.count(models.Product.id).label('count'),
        func.sum(models.Product.sku_amount).label('total_stock')
    ).filter(
        models.Product.sku_stock_local_id.isnot(None),
        models.Product.sku_stock_local_id != ""
    ).group_by(
        models.Product.sku_stock_local_id
    ).order_by(func.count(models.Product.id).desc()).limit(10).all()
    
    # Top características
    top_characteristics = db.query(
        models.Product.characteristic_name,
        models.Product.characteristic_value,
        func.count(models.Product.id).label('count')
    ).filter(
        models.Product.characteristic_name.isnot(None),
        models.Product.characteristic_name != ""
    ).group_by(
        models.Product.characteristic_name,
        models.Product.characteristic_value
    ).order_by(func.count(models.Product.id).desc()).limit(10).all()
    
    return {
        "products": {
            "total_products": total_products,
            "products_with_images": products_with_images,
            "products_with_stock": products_with_stock,
            "products_with_characteristics": products_with_characteristics
        },
        "images": {
            "total_images": int(total_images),
            "avg_images_per_product": float(avg_images_per_product)
        },
        "skus": {
            "total_skus": int(total_skus),
            "avg_skus_per_product": float(avg_skus_per_product),
            "total_stock": int(total_stock)
        },
        "characteristics": {
            "total_characteristics": int(total_characteristics),
            "avg_characteristics_per_product": float(avg_characteristics_per_product)
        },
        "prices": {
            "min_price": float(min_price),
            "max_price": float(max_price),
            "avg_price": float(avg_price)
        },
        "top_brands": [
            {
                "brand_name": stat.brand_name,
                "count": stat.count
            }
            for stat in top_brands
        ],
        "top_categories": [
            {
                "category_name": stat.category_name,
                "count": stat.count
            }
            for stat in top_categories
        ],
        "image_statuses": [
            {
                "status": stat.image_status,
                "count": stat.count
            }
            for stat in image_statuses
        ],
        "stock_locations": [
            {
                "stock_local_id": stat.sku_stock_local_id,
                "count": stat.count,
                "total_stock": int(stat.total_stock) if stat.total_stock else 0
            }
            for stat in stock_locations
        ],
        "top_characteristics": [
            {
                "name": stat.characteristic_name,
                "value": stat.characteristic_value,
                "count": stat.count
            }
            for stat in top_characteristics
        ]
    }

# =============================================================================
# ENDPOINT DE EXEMPLO ULTRA COMPLETO
# =============================================================================

@app.get("/examples/product-ultra-complete")
def get_product_ultra_complete_example(db: Session = Depends(get_db)):
    """Exemplo de produto com TODOS os campos ULTRA expandidos"""
    product = db.query(models.Product).first()
    
    if not product:
        return {"message": "Nenhum produto encontrado. Execute a sincronização primeiro."}
    
    return {
        "basic_fields": {
            "id": product.id,
            "anymarket_id": product.anymarket_id,
            "title": product.title,
            "description": product.description
        },
        "brand_category_expanded": {
            "brand_id": product.brand_id,
            "brand_name": product.brand_name,
            "brand_partner_id": product.brand_partner_id,
            "category_id": product.category_id,
            "category_name": product.category_name,
            "category_path": product.category_path
        },
        "images_expanded_NEW": {
            "image_id": product.image_id,
            "image_main": product.image_main,
            "image_url": product.image_url,
            "image_thumbnail_url": product.image_thumbnail_url,
            "image_standard_url": product.image_standard_url,
            "image_status": product.image_status,
            "image_standard_width": product.image_standard_width,
            "image_standard_height": product.image_standard_height,
            "total_images": product.total_images,
            "has_main_image": product.has_main_image,
            "main_image_url": product.main_image_url
        },
        "skus_expanded_NEW": {
            "sku_id": product.sku_id,
            "sku_title": product.sku_title,
            "sku_partner_id": product.sku_partner_id,
            "sku_ean": product.sku_ean,
            "sku_price": product.sku_price,
            "sku_amount": product.sku_amount,
            "sku_additional_time": product.sku_additional_time,
            "sku_stock_local_id": product.sku_stock_local_id,
            "total_skus": product.total_skus,
            "min_price": product.min_price,
            "max_price": product.max_price,
            "total_stock": product.total_stock,
            "avg_price": product.avg_price,
            "has_stock": product.has_stock
        },
        "characteristics_expanded_NEW": {
            "characteristic_index": product.characteristic_index,
            "characteristic_name": product.characteristic_name,
            "characteristic_value": product.characteristic_value,
            "total_characteristics": product.total_characteristics,
            "has_characteristics": product.has_characteristics
        },
        "json_data_complete": {
            "images_data": product.images,
            "skus_data": product.skus,
            "characteristics_data": product.characteristics
        }
    }

@app.get("/examples/structure-products-ultra-comparison")
def get_structure_products_ultra_comparison():
    """Comparação entre estrutura básica vs ultra expandida para produtos"""
    return {
        "antes_basic_structure": {
            "products": {
                "campos": ["id", "anymarket_id", "title", "description", "brand", "category", "price", "stock"],
                "total": 8,
                "images": "JSON completo apenas",
                "skus": "JSON completo apenas",
                "characteristics": "JSON completo apenas"
            }
        },
        "depois_ultra_expanded_structure": {
            "products": {
                "campos_basicos": 8,
                "category_expandida": 3,
                "brand_expandida": 4,
                "nbm_expandida": 2,
                "origin_expandida": 2,
                "images_expandida_NOVO": 15,
                "skus_expandida_NOVO": 13,
                "characteristics_expandida_NOVO": 5,
                "dimensoes_garantia": 6,
                "status_configuracoes": 8,
                "campos_derivados": 9,
                "total": 75,
                "images": "Expandido em colunas individuais + JSON completo",
                "skus": "Expandido em colunas individuais + JSON completo",
                "characteristics": "Expandido em colunas individuais + JSON completo"
            }
        },
        "novos_campos_images": [
            "image_id", "image_main", "image_url", "image_thumbnail_url",
            "image_standard_url", "image_status", "image_standard_width",
            "image_standard_height", "total_images", "has_main_image", "main_image_url"
        ],
        "novos_campos_skus": [
            "sku_id", "sku_title", "sku_partner_id", "sku_ean", "sku_price",
            "sku_amount", "sku_additional_time", "sku_stock_local_id",
            "total_skus", "min_price", "max_price", "total_stock", "avg_price", "has_stock"
        ],
        "novos_campos_characteristics": [
            "characteristic_index", "characteristic_name", "characteristic_value",
            "total_characteristics", "has_characteristics"
        ],
        "beneficios_ultra": [
            "Consultas SQL diretas em images, skus e characteristics",
            "Filtros por SKU Partner ID específico",
            "Análises de preços por faixa",
            "Relatórios de produtos com estoque",
            "Estatísticas por local de estoque",
            "Busca por características específicas",
            "Performance otimizada para BI",
            "Dados normalizados + JSON completo"
        ]
    }

# =============================================================================
# HEALTH CHECK ATUALIZADO PARA INCLUIR PRODUCTS
# =============================================================================

@app.get("/health-products")
def health_check_products(db: Session = Depends(get_db)):
    """Health check específico para produtos com campos expandidos"""
    try:
        # Testar conexão com banco
        products_count = db.query(models.Product).count()
        products_with_images = db.query(models.Product).filter(models.Product.has_main_image == True).count()
        products_with_stock = db.query(models.Product).filter(models.Product.has_stock == True).count()
        products_with_characteristics = db.query(models.Product).filter(models.Product.has_characteristics == True).count()
        
        # Testar alguns campos expandidos
        sample_product = db.query(models.Product).first()
        expanded_fields_working = False
        
        if sample_product:
            expanded_fields_working = all([
                hasattr(sample_product, 'image_url'),
                hasattr(sample_product, 'sku_partner_id'),
                hasattr(sample_product, 'characteristic_name'),
                hasattr(sample_product, 'total_images'),
                hasattr(sample_product, 'total_skus'),
                hasattr(sample_product, 'total_characteristics')
            ])
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": {
                "status": "ok",
                "products_count": products_count,
                "products_with_images": products_with_images,
                "products_with_stock": products_with_stock,
                "products_with_characteristics": products_with_characteristics
            },
            "expanded_fields": {
                "status": "ok" if expanded_fields_working else "error",
                "images_expanded": expanded_fields_working,
                "skus_expanded": expanded_fields_working,
                "characteristics_expanded": expanded_fields_working
            },
            "version": "4.0.0 - PRODUCTS ULTRA COMPLETOS",
            "features": [
                "Products com images, skus e characteristics expandidos",
                "~75 campos expandidos por produto",
                "Consultas SQL diretas em todos os campos",
                "Endpoints especializados para busca avançada"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# =============================================================================
# ENDPOINT DE BUSCA AVANÇADA COMBINADA
# =============================================================================

@app.get("/products/advanced-search")
def advanced_search_products(
    title: Optional[str] = Query(None, description="Buscar no título"),
    brand: Optional[str] = Query(None, description="Buscar na marca"),
    category: Optional[str] = Query(None, description="Buscar na categoria"),
    min_price: Optional[float] = Query(None, description="Preço mínimo"),
    max_price: Optional[float] = Query(None, description="Preço máximo"),
    with_stock: Optional[bool] = Query(None, description="Apenas com estoque"),
    with_images: Optional[bool] = Query(None, description="Apenas com imagens"),
    sku_partner_id: Optional[str] = Query(None, description="SKU Partner ID"),
    ean: Optional[str] = Query(None, description="Código EAN"),
    characteristic_name: Optional[str] = Query(None, description="Nome da característica"),
    characteristic_value: Optional[str] = Query(None, description="Valor da característica"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Busca avançada combinando múltiplos campos expandidos"""
    
    query = db.query(models.Product)
    
    if title:
        query = query.filter(models.Product.title.ilike(f"%{title}%"))
    
    if brand:
        query = query.filter(models.Product.brand_name.ilike(f"%{brand}%"))
    
    if category:
        query = query.filter(models.Product.category_name.ilike(f"%{category}%"))
    
    if min_price is not None:
        query = query.filter(models.Product.sku_price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.Product.sku_price <= max_price)
    
    if with_stock is not None:
        query = query.filter(models.Product.has_stock == with_stock)
    
    if with_images is not None:
        query = query.filter(models.Product.has_main_image == with_images)
    
    if sku_partner_id:
        query = query.filter(models.Product.sku_partner_id.ilike(f"%{sku_partner_id}%"))
    
    if ean:
        query = query.filter(models.Product.sku_ean == ean)
    
    if characteristic_name:
        query = query.filter(models.Product.characteristic_name.ilike(f"%{characteristic_name}%"))
    
    if characteristic_value:
        query = query.filter(models.Product.characteristic_value.ilike(f"%{characteristic_value}%"))
    
    products = query.offset(skip).limit(limit).all()
    
    return {
        "total_found": query.count(),
        "products": products,
        "search_params": {
            "title": title,
            "brand": brand,
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "with_stock": with_stock,
            "with_images": with_images,
            "sku_partner_id": sku_partner_id,
            "ean": ean,
            "characteristic_name": characteristic_name,
            "characteristic_value": characteristic_value
        }
    }