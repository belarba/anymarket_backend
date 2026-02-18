from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base
from sqlalchemy.dialects.postgresql import JSONB


class Product(Base):
    __tablename__ = "products"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    external_id_product = Column(String)
    
    # Category expandida (objeto category → colunas individuais)
    category_id = Column(String)
    category_name = Column(String)
    category_path = Column(String)
    
    # Brand expandida (objeto brand → colunas individuais)
    brand_id = Column(String)
    brand_name = Column(String)
    brand_reduced_name = Column(String)
    brand_partner_id = Column(String)
    
    # NBM expandido (objeto nbm → colunas individuais)
    nbm_id = Column(String)
    nbm_description = Column(String)
    
    # Origin expandido (objeto origin → colunas individuais)
    origin_id = Column(String)
    origin_description = Column(String)
    
    # Informações básicas do produto
    model = Column(String)
    video_url = Column(String)
    gender = Column(String)
    
    # Garantia
    warranty_time = Column(Integer)
    warranty_text = Column(Text)
    
    # Dimensões e peso
    height = Column(Float)
    width = Column(Float)
    weight = Column(Float)
    length = Column(Float)
    
    # Preços e configurações
    price_factor = Column(Float)
    calculated_price = Column(Boolean, default=False)
    definition_price_scope = Column(String)
    
    # Status e configurações do produto
    has_variations = Column(Boolean, default=False)
    is_product_active = Column(Boolean, default=True)
    product_type = Column(String)
    allow_automatic_sku_marketplace_creation = Column(Boolean, default=True)
    
    # ========================================================================
    # IMAGES EXPANDIDAS - Primeira imagem do array images
    # ========================================================================
    
    # Image principal (images[0])
    image_id = Column(String)  # images[0].id
    image_index = Column(Integer)  # images[0].index
    image_main = Column(Boolean, default=False)  # images[0].main
    image_url = Column(String)  # images[0].url
    image_thumbnail_url = Column(String)  # images[0].thumbnailUrl
    image_low_resolution_url = Column(String)  # images[0].lowResolutionUrl
    image_standard_url = Column(String)  # images[0].standardUrl
    image_original_image = Column(String)  # images[0].originalImage
    image_status = Column(String)  # images[0].status
    image_standard_width = Column(Integer)  # images[0].standardWidth
    image_standard_height = Column(Integer)  # images[0].standardHeight
    image_original_width = Column(Integer)  # images[0].originalWidth
    image_original_height = Column(Integer)  # images[0].originalHeight
    image_product_id = Column(String)  # images[0].productId
    
    # Campos derivados das images
    total_images = Column(Integer, default=0)  # Total de imagens
    has_main_image = Column(Boolean, default=False)  # Tem imagem principal
    main_image_url = Column(String)  # URL da imagem principal
    
    # ========================================================================
    # SKUS EXPANDIDOS - Primeiro SKU do array skus
    # ========================================================================
    
    # SKU principal (skus[0])
    sku_id = Column(String)  # skus[0].id
    sku_title = Column(String)  # skus[0].title
    sku_partner_id = Column(String)  # skus[0].partnerId
    sku_ean = Column(String)  # skus[0].ean
    sku_price = Column(Float)  # skus[0].price
    sku_amount = Column(Integer)  # skus[0].amount
    sku_additional_time = Column(Integer)  # skus[0].additionalTime
    sku_stock_local_id = Column(String)  # skus[0].stockLocalId
    
    # Campos derivados dos SKUs
    total_skus = Column(Integer, default=0)  # Total de SKUs
    min_price = Column(Float)  # Menor preço entre SKUs
    max_price = Column(Float)  # Maior preço entre SKUs
    total_stock = Column(Integer, default=0)  # Soma do estoque de todos os SKUs
    avg_price = Column(Float)  # Preço médio dos SKUs
    has_stock = Column(Boolean, default=False)  # Tem estoque disponível
    
    # ========================================================================
    # CHARACTERISTICS EXPANDIDAS - Primeira característica do array characteristics
    # ========================================================================
    
    # Characteristic principal (characteristics[0])
    characteristic_index = Column(Integer)  # characteristics[0].index
    characteristic_name = Column(String)  # characteristics[0].name
    characteristic_value = Column(String)  # characteristics[0].value
    
    # Campos derivados das characteristics
    total_characteristics = Column(Integer, default=0)  # Total de características
    has_characteristics = Column(Boolean, default=False)  # Tem características
    
    # ========================================================================
    # CAMPOS DERIVADOS PARA FACILITAR CONSULTAS
    # ========================================================================
    
    # Campos legados (compatibilidade)
    sku = Column(String, index=True)  # SKU principal (sku_partner_id)
    price = Column(Float)  # Preço principal (sku_price)
    stock_quantity = Column(Integer, default=0)  # Estoque principal (sku_amount)
    active = Column(Boolean, default=True)  # Produto ativo
    
    # ========================================================================
    # DADOS JSON COMPLETOS (para referência completa)
    # ========================================================================
    characteristics = Column(JSON)  # Array completo de características
    images = Column(JSON)  # Array completo de imagens
    skus = Column(JSON)  # Array completo de SKUs
    
    # Status de sincronização
    sync_status = Column(String, default="pending")
    sync_error_message = Column(Text)
    last_sync_date = Column(DateTime)
    last_sync_attempt = Column(DateTime)
    
    # Metadados do sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(anymarket_id='{self.anymarket_id}', title='{self.title}', price={self.price})>"

# Manter a classe Order inalterada (já está completa)
class Order(Base):
    __tablename__ = "orders"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    account_name = Column(String)
    market_place_id = Column(String)
    market_place_number = Column(String)
    partner_id = Column(String)
    marketplace = Column(String)
    sub_channel = Column(String)
    sub_channel_normalized = Column(String)
    
    # Datas importantes
    created_at_anymarket = Column(DateTime)
    payment_date = Column(DateTime)
    cancel_date = Column(DateTime)
    
    # Status e informações do pedido
    shipping_option_id = Column(String)
    transmission_status = Column(String)
    status = Column(String)
    market_place_status = Column(String)
    market_place_status_complement = Column(String)
    market_place_shipment_status = Column(String)
    
    # Documentos e intermediários
    document_intermediator = Column(String)
    intermediate_registration_id = Column(String)
    document_payment_institution = Column(String)
    fulfillment = Column(Boolean, default=False)
    
    # Cotação
    quote_id = Column(String)
    quote_price = Column(Float)
    
    # Valores financeiros
    discount = Column(Float)
    freight = Column(Float)
    seller_freight = Column(Float)
    interest_value = Column(Float)
    gross = Column(Float)
    total = Column(Float)
    
    # URLs
    market_place_url = Column(String)
    
    # Invoice (nota fiscal) - expandido
    invoice_access_key = Column(String)
    invoice_series = Column(String)
    invoice_number = Column(String)
    invoice_date = Column(DateTime)
    invoice_cfop = Column(String)
    invoice_company_state_tax_id = Column(String)
    invoice_link_nfe = Column(String)
    invoice_link = Column(String)
    invoice_extra_description = Column(String)
    
    # Shipping (endereço de entrega) - expandido
    shipping_address = Column(String)
    shipping_city = Column(String)
    shipping_comment = Column(String)
    shipping_country = Column(String)
    shipping_country_acronym_normalized = Column(String)
    shipping_country_name_normalized = Column(String)
    shipping_neighborhood = Column(String)
    shipping_number = Column(String)
    shipping_promised_shipping_time = Column(DateTime)
    shipping_promised_dispatch_time = Column(DateTime)
    shipping_receiver_name = Column(String)
    shipping_reference = Column(String)
    shipping_state = Column(String)
    shipping_state_name_normalized = Column(String)
    shipping_street = Column(String)
    shipping_zip_code = Column(String)
    
    # Billing Address (endereço de cobrança) - expandido
    billing_address = Column(String)
    billing_city = Column(String)
    billing_comment = Column(String)
    billing_country = Column(String)
    billing_country_acronym_normalized = Column(String)
    billing_country_name_normalized = Column(String)
    billing_neighborhood = Column(String)
    billing_number = Column(String)
    billing_reference = Column(String)
    billing_shipment_user_document = Column(String)
    billing_shipment_user_document_type = Column(String)
    billing_shipment_user_name = Column(String)
    billing_state = Column(String)
    billing_state_name_normalized = Column(String)
    billing_street = Column(String)
    billing_zip_code = Column(String)
    
    # Anymarket Address - expandido
    anymarket_address = Column(String)
    anymarket_city = Column(String)
    anymarket_comment = Column(String)
    anymarket_country = Column(String)
    anymarket_neighborhood = Column(String)
    anymarket_number = Column(String)
    anymarket_promised_shipping_time = Column(DateTime)
    anymarket_receiver_name = Column(String)
    anymarket_reference = Column(String)
    anymarket_state = Column(String)
    anymarket_state_acronym_normalized = Column(String)
    anymarket_street = Column(String)
    anymarket_zip_code = Column(String)
    
    # Buyer (comprador) - expandido
    buyer_cell_phone = Column(String)
    buyer_document = Column(String)
    buyer_document_number_normalized = Column(String)
    buyer_document_type = Column(String)
    buyer_email = Column(String)
    buyer_market_place_id = Column(String)
    buyer_name = Column(String)
    buyer_phone = Column(String)
    buyer_date_of_birth = Column(DateTime)
    buyer_company_state_tax_id = Column(String)
    
    # Tracking (rastreamento) - expandido
    tracking_carrier = Column(String)
    tracking_date = Column(DateTime)
    tracking_delivered_date = Column(DateTime)
    tracking_estimate_date = Column(DateTime)
    tracking_number = Column(String)
    tracking_shipped_date = Column(DateTime)
    tracking_url = Column(String)
    tracking_carrier_document = Column(String)
    tracking_buffering_date = Column(DateTime)
    tracking_delivery_status = Column(String)
    
    # Pickup (retirada) - expandido
    pickup_id = Column(Integer)
    pickup_description = Column(String)
    pickup_partner_id = Column(Integer)
    pickup_marketplace_id = Column(String)
    pickup_receiver_name = Column(String)
    
    # ID Account
    id_account = Column(Integer)
    
    # Metadados - expandidos
    metadata_number_of_packages = Column(String)
    metadata_cd_zip_code = Column(String)
    metadata_need_invoice_xml = Column(String)
    metadata_mshops = Column(String)
    metadata_envvias = Column(String)
    metadata_via_total_discount_amount = Column(String)
    metadata_b2w_shipping_type = Column(String)
    metadata_logistic_type = Column(String)
    metadata_print_tag = Column(String)
    metadata_cancel_detail_motivation = Column(String)
    metadata_cancel_detail_code = Column(String)
    metadata_cancel_detail_description = Column(String)
    metadata_cancel_detail_requested_by = Column(String)
    metadata_order_type_name = Column(String)
    metadata_shipping_id = Column(String)
    
    # ITEMS EXPANDIDOS
    item_product_id = Column(String)
    item_product_title = Column(String)
    item_sku_id = Column(String)
    item_sku_title = Column(String)
    item_sku_partner_id = Column(String)
    item_sku_ean = Column(String)
    item_amount = Column(Float)
    item_unit = Column(Float)
    item_gross = Column(Float)
    item_total = Column(Float)
    item_discount = Column(Float)
    item_id_in_marketplace = Column(String)
    item_order_item_id = Column(String)
    item_free_shipping = Column(Boolean, default=False)
    item_is_catalog = Column(Boolean, default=False)
    item_id_in_marketplace_catalog_origin = Column(String)
    item_shipping_id = Column(String)
    item_shipping_type = Column(String)
    item_shipping_carrier_normalized = Column(String)
    item_shipping_carrier_type_normalized = Column(String)
    item_stock_local_id = Column(String)
    item_stock_amount = Column(Float)
    item_stock_name = Column(String)
    total_items = Column(Integer, default=0)
    total_items_amount = Column(Float, default=0)
    total_items_value = Column(Float, default=0)
    
    # PAYMENTS EXPANDIDOS
    payment_method = Column(String)
    payment_status = Column(String)
    payment_value = Column(Float)
    payment_marketplace_id = Column(String)
    payment_method_normalized = Column(String)
    payment_detail_normalized = Column(String)
    total_payments = Column(Integer, default=0)
    total_payments_value = Column(Float, default=0)
    
    # DADOS JSON COMPLETOS
    items_data = Column(JSON)
    payments_data = Column(JSON)
    shippings_data = Column(JSON)
    stocks_data = Column(JSON)
    metadata_extra = Column(JSON)
    
    # Metadados do sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Order(anymarket_id='{self.anymarket_id}', status='{self.status}', total={self.total})>"

class Stock(Base):
    __tablename__ = "stocks"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    
    # Stock Keeping Unit (SKU) expandido
    sku_id = Column(String, index=True)
    sku_title = Column(String)
    sku_partner_id = Column(String, index=True)
    
    # Stock Local expandido
    stock_local_id = Column(String, index=True)
    stock_local_oi_value = Column(String)
    stock_local_name = Column(String)
    stock_local_virtual = Column(Boolean, default=False)
    stock_local_default_local = Column(Boolean, default=False)
    stock_local_priority_points = Column(Integer)
    
    # Quantidades
    amount = Column(Integer, default=0)
    reservation_amount = Column(Integer, default=0)
    available_amount = Column(Integer, default=0)
    
    # Informações adicionais
    price = Column(Float)
    active = Column(Boolean, default=True)
    additional_time = Column(Integer, default=0)
    last_stock_update = Column(String)
    last_stock_update_parsed = Column(DateTime)
    
    # Dados JSON completos para referência
    stock_keeping_unit_data = Column(JSON)
    stock_local_data = Column(JSON)
    
    # Chave única composta (sku_id + stock_local_id)
    sku_stock_key = Column(String, unique=True, index=True)
    
    # Status de sincronização
    sync_status = Column(String, default="pending")
    sync_error_message = Column(Text)
    last_sync_date = Column(DateTime)
    
    # Metadados do sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Stock(sku_id='{self.sku_id}', stock_local='{self.stock_local_name}', amount={self.amount})>"


class SkuMarketplace(Base):
    """
    Model para armazenar dados de SKUs nos marketplaces
    Endpoint: /skus/marketplaces
    """
    __tablename__ = "sku_marketplaces"
    
    # Chave primária interna
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ID do Anymarket (identificador único da API)
    anymarket_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # Campos principais
    account_name = Column(String(255), nullable=True)
    id_account = Column(Integer, nullable=True)
    marketplace = Column(String(100), nullable=True, index=True)
    id_in_marketplace = Column(String(255), nullable=True, index=True)
    index = Column(Integer, nullable=True)
    publication_status = Column(String(50), nullable=True, index=True)
    marketplace_status = Column(String(100), nullable=True)
    price = Column(Float, nullable=True)
    price_factor = Column(Float, nullable=True)
    discount_price = Column(Float, nullable=True)
    permalink = Column(Text, nullable=True)
    sku_in_marketplace = Column(String(255), nullable=True, index=True)
    marketplace_item_code = Column(String(255), nullable=True)
    
    # FIELDS expandidos
    field_title = Column(String(500), nullable=True)
    field_template = Column(Integer, nullable=True)
    field_price_factor = Column(String(50), nullable=True)
    field_discount_type = Column(String(50), nullable=True)
    field_discount_value = Column(String(50), nullable=True)
    field_has_discount = Column(Boolean, nullable=True)
    field_concat_attributes = Column(Text, nullable=True)
    field_delivery_type = Column(String(100), nullable=True)
    field_shipment = Column(String(255), nullable=True)
    field_cross_docking = Column(String(100), nullable=True)
    field_custom_description = Column(Text, nullable=True)
    field_ean = Column(String(100), nullable=True)
    field_manufacturing_time = Column(String(50), nullable=True)
    field_value = Column(String(100), nullable=True)
    field_percent = Column(String(50), nullable=True)
    
    # Campos de preço por nível (Mercado Livre)
    field_bronze_price = Column(String(50), nullable=True)
    field_bronze_price_factor = Column(String(50), nullable=True)
    field_silver_price = Column(String(50), nullable=True)
    field_silver_price_factor = Column(String(50), nullable=True)
    field_gold_price = Column(String(50), nullable=True)
    field_gold_price_factor = Column(String(50), nullable=True)
    field_gold_premium_price = Column(String(50), nullable=True)
    field_gold_premium_price_factor = Column(String(50), nullable=True)
    field_gold_pro_price = Column(String(50), nullable=True)
    field_gold_pro_price_factor = Column(String(50), nullable=True)
    field_gold_special_price = Column(String(50), nullable=True)
    field_gold_special_price_factor = Column(String(50), nullable=True)
    field_free_price = Column(String(50), nullable=True)
    field_free_price_factor = Column(String(50), nullable=True)
    
    # Campos de configuração de venda
    field_buying_mode = Column(String(50), nullable=True)
    field_category_with_variation = Column(String(255), nullable=True)
    field_condition = Column(String(50), nullable=True)
    field_free_shipping = Column(Boolean, nullable=True)
    field_listing_type_id = Column(String(100), nullable=True)
    field_shipping_local_pick_up = Column(Boolean, nullable=True)
    field_shipping_mode = Column(String(50), nullable=True)
    field_measurement_chart_id = Column(String(100), nullable=True)
    field_warranty_time = Column(String(50), nullable=True)
    field_has_fulfillment = Column(Boolean, nullable=True)
    field_official_store_id = Column(String(100), nullable=True)
    field_ml_channels = Column(String(100), nullable=True)
    field_is_main_sku = Column(Boolean, nullable=True)
    field_is_match = Column(Boolean, nullable=True)
    
    # Warnings
    warnings_count = Column(Integer, nullable=True, default=0)
    has_warnings = Column(Boolean, nullable=True, default=False)
    
    # Dados JSON completos
    fields_data = Column(JSONB, nullable=True)
    attributes_data = Column(JSONB, nullable=True)
    warnings_data = Column(JSONB, nullable=True)
    
    # Campos de controle
    sync_status = Column(String(50), nullable=True, default='synced')
    last_sync_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    def __repr__(self):
        return f"<SkuMarketplace(id={self.id}, anymarket_id={self.anymarket_id}, marketplace={self.marketplace})>"

class Transmission(Base):
    """
    Model para armazenar dados de transmissões
    Endpoint: /transmissions
    """
    __tablename__ = "transmissions"
    
    # Chave primária interna
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ID do Anymarket
    anymarket_id = Column(String(50), nullable=False, unique=True, index=True)
    
    # Campos principais
    account_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    model = Column(String(255), nullable=True)
    video_url = Column(Text, nullable=True)
    warranty_time = Column(Integer, nullable=True)
    warranty_text = Column(Text, nullable=True)
    
    # Dimensões
    height = Column(Float, nullable=True)
    width = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    length = Column(Float, nullable=True)
    
    # Status
    status = Column(String(100), nullable=True, index=True)
    transmission_message = Column(Text, nullable=True)
    publication_status = Column(String(50), nullable=True, index=True)
    marketplace_status = Column(String(100), nullable=True)
    price_factor = Column(Float, nullable=True)
    
    # Category expandido
    category_id = Column(String(50), nullable=True)
    category_name = Column(String(255), nullable=True)
    category_path = Column(Text, nullable=True)
    
    # Brand expandido
    brand_id = Column(String(50), nullable=True)
    brand_name = Column(String(255), nullable=True)
    
    # Product expandido
    product_id = Column(String(50), nullable=True, index=True)
    product_title = Column(String(500), nullable=True)
    
    # NBM expandido
    nbm_id = Column(String(50), nullable=True)
    nbm_description = Column(Text, nullable=True)
    
    # Origin expandido
    origin_id = Column(String(50), nullable=True)
    origin_description = Column(String(255), nullable=True)
    
    # SKU expandido
    sku_id = Column(String(50), nullable=True, index=True)
    sku_title = Column(String(500), nullable=True)
    sku_partner_id = Column(String(100), nullable=True, index=True)
    sku_ean = Column(String(100), nullable=True)
    sku_price = Column(Float, nullable=True)
    sku_amount = Column(Integer, nullable=True)
    sku_discount_price = Column(Float, nullable=True)
    
    # SKU Variations (primeiro item expandido)
    variation_id = Column(String(50), nullable=True)
    variation_description = Column(String(255), nullable=True)
    variation_type_id = Column(String(50), nullable=True)
    variation_type_name = Column(String(255), nullable=True)
    variation_visual = Column(Boolean, nullable=True)
    total_variations = Column(Integer, nullable=True, default=0)
    
    # Characteristics (primeiro item expandido)
    characteristic_index = Column(Integer, nullable=True)
    characteristic_name = Column(String(255), nullable=True)
    characteristic_value = Column(Text, nullable=True)
    total_characteristics = Column(Integer, nullable=True, default=0)
    
    # Images (primeiro item expandido)
    image_id = Column(String(50), nullable=True)
    image_index = Column(Integer, nullable=True)
    image_main = Column(Boolean, nullable=True)
    image_url = Column(Text, nullable=True)
    image_thumbnail_url = Column(Text, nullable=True)
    image_status = Column(String(50), nullable=True)
    image_status_message = Column(Text, nullable=True)
    total_images = Column(Integer, nullable=True, default=0)
    main_image_url = Column(Text, nullable=True)
    
    # Dados JSON completos
    category_data = Column(JSON, nullable=True)
    brand_data = Column(JSON, nullable=True)
    product_data = Column(JSON, nullable=True)
    nbm_data = Column(JSON, nullable=True)
    origin_data = Column(JSON, nullable=True)
    sku_data = Column(JSON, nullable=True)
    characteristics_data = Column(JSON, nullable=True)
    images_data = Column(JSON, nullable=True)
    
    # Campos de controle
    sync_status = Column(String(50), nullable=True, default='synced')
    last_sync_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=True, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, onupdate=func.now())
    
    def __repr__(self):
        return f"<Transmission(id={self.id}, anymarket_id={self.anymarket_id}, status={self.status})>"