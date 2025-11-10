from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

# Schemas para Products - ULTRA EXPANDIDOS com Images, SKUs e Characteristics
class ProductBase(BaseModel):
    # Campos básicos
    title: Optional[str] = None
    description: Optional[str] = None
    external_id_product: Optional[str] = None
    
    # Category expandida
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_path: Optional[str] = None
    
    # Brand expandida
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    brand_reduced_name: Optional[str] = None
    brand_partner_id: Optional[str] = None
    
    # NBM expandido
    nbm_id: Optional[str] = None
    nbm_description: Optional[str] = None
    
    # Origin expandido
    origin_id: Optional[str] = None
    origin_description: Optional[str] = None
    
    # Informações básicas do produto
    model: Optional[str] = None
    video_url: Optional[str] = None
    gender: Optional[str] = None
    
    # Garantia
    warranty_time: Optional[int] = None
    warranty_text: Optional[str] = None
    
    # Dimensões e peso
    height: Optional[float] = None
    width: Optional[float] = None
    weight: Optional[float] = None
    length: Optional[float] = None
    
    # Preços e configurações
    price_factor: Optional[float] = None
    calculated_price: Optional[bool] = False
    definition_price_scope: Optional[str] = None
    
    # Status e configurações do produto
    has_variations: Optional[bool] = False
    is_product_active: Optional[bool] = True
    product_type: Optional[str] = None
    allow_automatic_sku_marketplace_creation: Optional[bool] = True
    
    # ========================================================================
    # IMAGES EXPANDIDAS (NOVOS CAMPOS)
    # ========================================================================
    image_id: Optional[str] = None
    image_index: Optional[int] = None
    image_main: Optional[bool] = None
    image_url: Optional[str] = None
    image_thumbnail_url: Optional[str] = None
    image_low_resolution_url: Optional[str] = None
    image_standard_url: Optional[str] = None
    image_original_image: Optional[str] = None
    image_status: Optional[str] = None
    image_standard_width: Optional[int] = None
    image_standard_height: Optional[int] = None
    image_original_width: Optional[int] = None
    image_original_height: Optional[int] = None
    image_product_id: Optional[str] = None
    total_images: Optional[int] = None
    has_main_image: Optional[bool] = None
    main_image_url: Optional[str] = None
    
    # ========================================================================
    # SKUS EXPANDIDOS (NOVOS CAMPOS)
    # ========================================================================
    sku_id: Optional[str] = None
    sku_title: Optional[str] = None
    sku_partner_id: Optional[str] = None
    sku_ean: Optional[str] = None
    sku_price: Optional[float] = None
    sku_amount: Optional[int] = None
    sku_additional_time: Optional[int] = None
    sku_stock_local_id: Optional[str] = None
    total_skus: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    total_stock: Optional[int] = None
    avg_price: Optional[float] = None
    has_stock: Optional[bool] = None
    
    # ========================================================================
    # CHARACTERISTICS EXPANDIDAS (NOVOS CAMPOS)
    # ========================================================================
    characteristic_index: Optional[int] = None
    characteristic_name: Optional[str] = None
    characteristic_value: Optional[str] = None
    total_characteristics: Optional[int] = None
    has_characteristics: Optional[bool] = None
    
    # Campos legados (compatibilidade)
    sku: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = 0
    active: Optional[bool] = True
    
    # Dados JSON completos
    characteristics: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None
    skus: Optional[List[Dict[str, Any]]] = None
    
    # Status de sincronização
    sync_status: Optional[str] = "pending"
    sync_error_message: Optional[str] = None
    last_sync_date: Optional[datetime] = None
    last_sync_attempt: Optional[datetime] = None

class ProductCreate(ProductBase):
    anymarket_id: str

class Product(ProductBase):
    id: int
    anymarket_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProductSummary(BaseModel):
    id: int
    anymarket_id: str
    title: str
    sku_partner_id: Optional[str]
    brand_name: Optional[str]
    category_name: Optional[str]
    sku_price: Optional[float]
    sku_amount: Optional[int]
    total_skus: Optional[int]
    total_images: Optional[int]
    has_variations: Optional[bool]
    active: Optional[bool]
    sync_status: Optional[str]
    main_image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas específicos para Images expandidas
class ProductImage(BaseModel):
    anymarket_id: Optional[str]
    image_id: Optional[str]
    image_main: Optional[bool]
    image_url: Optional[str]
    image_thumbnail_url: Optional[str]
    image_standard_url: Optional[str]
    image_original_image: Optional[str]
    image_status: Optional[str]
    image_standard_width: Optional[int]
    image_standard_height: Optional[int]
    total_images: Optional[int]
    has_main_image: Optional[bool]

    class Config:
        from_attributes = True

# Schemas específicos para SKUs expandidos
class ProductSku(BaseModel):
    anymarket_id: Optional[str]
    sku_id: Optional[str]
    sku_title: Optional[str]
    sku_partner_id: Optional[str]
    sku_ean: Optional[str]
    sku_price: Optional[float]
    sku_amount: Optional[int]
    sku_additional_time: Optional[int]
    sku_stock_local_id: Optional[str]
    total_skus: Optional[int]
    min_price: Optional[float]
    max_price: Optional[float]
    total_stock: Optional[int]
    avg_price: Optional[float]
    has_stock: Optional[bool]

    class Config:
        from_attributes = True

# Schemas específicos para Characteristics expandidas
class ProductCharacteristic(BaseModel):
    anymarket_id: Optional[str]
    characteristic_index: Optional[int]
    characteristic_name: Optional[str]
    characteristic_value: Optional[str]
    total_characteristics: Optional[int]
    has_characteristics: Optional[bool]

    class Config:
        from_attributes = True

# Schema para estatísticas detalhadas
class ProductImageStats(BaseModel):
    status: str
    count: int
    total_images: int

class ProductSkuStats(BaseModel):
    stock_local_id: str
    count: int
    total_stock: int
    avg_price: float

class ProductCharacteristicStats(BaseModel):
    name: str
    value: str
    count: int

class ProductStatisticsDetailed(BaseModel):
    products: Dict[str, int]
    images: Dict[str, int]
    skus: Dict[str, float]
    characteristics: Dict[str, int]
    top_brands: List[Dict[str, Any]]
    top_categories: List[Dict[str, Any]]
    top_image_statuses: List[ProductImageStats]
    top_stock_locations: List[ProductSkuStats]
    top_characteristics: List[ProductCharacteristicStats]

# Manter os schemas de Order inalterados (já estão completos)
class OrderBase(BaseModel):
    # Campos básicos
    anymarket_id: Optional[str] = None
    account_name: Optional[str] = None
    market_place_id: Optional[str] = None
    market_place_number: Optional[str] = None
    partner_id: Optional[str] = None
    marketplace: Optional[str] = None
    sub_channel: Optional[str] = None
    sub_channel_normalized: Optional[str] = None
    
    # Datas importantes
    created_at_anymarket: Optional[datetime] = None
    payment_date: Optional[datetime] = None
    cancel_date: Optional[datetime] = None
    
    # Status e informações do pedido
    shipping_option_id: Optional[str] = None
    transmission_status: Optional[str] = None
    status: Optional[str] = None
    market_place_status: Optional[str] = None
    market_place_status_complement: Optional[str] = None
    market_place_shipment_status: Optional[str] = None
    
    # Valores financeiros
    discount: Optional[float] = None
    freight: Optional[float] = None
    seller_freight: Optional[float] = None
    interest_value: Optional[float] = None
    gross: Optional[float] = None
    total: Optional[float] = None
    
    # Buyer expandido
    buyer_cell_phone: Optional[str] = None
    buyer_document: Optional[str] = None
    buyer_document_number_normalized: Optional[str] = None
    buyer_document_type: Optional[str] = None
    buyer_email: Optional[str] = None
    buyer_market_place_id: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_phone: Optional[str] = None
    buyer_date_of_birth: Optional[datetime] = None
    buyer_company_state_tax_id: Optional[str] = None
    
    # Shipping expandido
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_comment: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_country_acronym_normalized: Optional[str] = None
    shipping_country_name_normalized: Optional[str] = None
    shipping_neighborhood: Optional[str] = None
    shipping_number: Optional[str] = None
    shipping_promised_shipping_time: Optional[datetime] = None
    shipping_promised_dispatch_time: Optional[datetime] = None
    shipping_receiver_name: Optional[str] = None
    shipping_reference: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_state_name_normalized: Optional[str] = None
    shipping_street: Optional[str] = None
    shipping_zip_code: Optional[str] = None
    
    # Invoice expandido
    invoice_access_key: Optional[str] = None
    invoice_series: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    invoice_cfop: Optional[str] = None
    invoice_company_state_tax_id: Optional[str] = None
    invoice_link_nfe: Optional[str] = None
    invoice_link: Optional[str] = None
    invoice_extra_description: Optional[str] = None
    
    # Tracking expandido
    tracking_carrier: Optional[str] = None
    tracking_date: Optional[datetime] = None
    tracking_delivered_date: Optional[datetime] = None
    tracking_estimate_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    tracking_shipped_date: Optional[datetime] = None
    tracking_url: Optional[str] = None
    tracking_carrier_document: Optional[str] = None
    tracking_buffering_date: Optional[datetime] = None
    tracking_delivery_status: Optional[str] = None
    
    # ITEMS EXPANDIDOS
    item_product_id: Optional[str] = None
    item_product_title: Optional[str] = None
    item_sku_id: Optional[str] = None
    item_sku_title: Optional[str] = None
    item_sku_partner_id: Optional[str] = None
    item_sku_ean: Optional[str] = None
    item_amount: Optional[float] = None
    item_unit: Optional[float] = None
    item_gross: Optional[float] = None
    item_total: Optional[float] = None
    item_discount: Optional[float] = None
    item_id_in_marketplace: Optional[str] = None
    item_order_item_id: Optional[str] = None
    item_free_shipping: Optional[bool] = None
    item_is_catalog: Optional[bool] = None
    item_id_in_marketplace_catalog_origin: Optional[str] = None
    item_shipping_id: Optional[str] = None
    item_shipping_type: Optional[str] = None
    item_shipping_carrier_normalized: Optional[str] = None
    item_shipping_carrier_type_normalized: Optional[str] = None
    item_stock_local_id: Optional[str] = None
    item_stock_amount: Optional[float] = None
    item_stock_name: Optional[str] = None
    total_items: Optional[int] = None
    total_items_amount: Optional[float] = None
    total_items_value: Optional[float] = None
    
    # PAYMENTS EXPANDIDOS
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    payment_value: Optional[float] = None
    payment_marketplace_id: Optional[str] = None
    payment_method_normalized: Optional[str] = None
    payment_detail_normalized: Optional[str] = None
    total_payments: Optional[int] = None
    total_payments_value: Optional[float] = None
    
    # Dados JSON completos
    items_data: Optional[List[Dict[str, Any]]] = None
    payments_data: Optional[List[Dict[str, Any]]] = None
    shippings_data: Optional[List[Dict[str, Any]]] = None
    stocks_data: Optional[List[Dict[str, Any]]] = None
    metadata_extra: Optional[Dict[str, Any]] = None

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema resumido para listagens
class OrderSummary(BaseModel):
    id: int
    anymarket_id: Optional[str]
    marketplace: Optional[str]
    status: Optional[str]
    total: Optional[float]
    buyer_name: Optional[str]
    buyer_email: Optional[str]
    total_items: Optional[int]
    payment_method_normalized: Optional[str]
    item_product_title: Optional[str]
    created_at_anymarket: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas específicos para Items expandidos
class OrderItem(BaseModel):
    anymarket_id: Optional[str]
    item_product_id: Optional[str]
    item_product_title: Optional[str]
    item_sku_id: Optional[str]
    item_sku_title: Optional[str]
    item_sku_partner_id: Optional[str]
    item_sku_ean: Optional[str]
    item_amount: Optional[float]
    item_unit: Optional[float]
    item_total: Optional[float]
    item_free_shipping: Optional[bool]
    item_stock_name: Optional[str]
    total_items: Optional[int]
    total_items_value: Optional[float]

    class Config:
        from_attributes = True

# Schemas específicos para Payments expandidos
class OrderPayment(BaseModel):
    anymarket_id: Optional[str]
    payment_method: Optional[str]
    payment_status: Optional[str]
    payment_value: Optional[float]
    payment_method_normalized: Optional[str]
    payment_detail_normalized: Optional[str]
    total_payments: Optional[int]
    total_payments_value: Optional[float]

    class Config:
        from_attributes = True

# Schema para estatísticas detalhadas
class OrderItemStats(BaseModel):
    product_title: str
    orders_count: int
    total_quantity: float

class OrderPaymentStats(BaseModel):
    method: str
    orders_count: int
    total_value: float

class OrderStatisticsDetailed(BaseModel):
    orders: Dict[str, int]
    items: Dict[str, float]
    payments: Dict[str, float]
    top_products: List[OrderItemStats]
    top_payment_methods: List[OrderPaymentStats]

# Schemas para Stock
class StockBase(BaseModel):
    sku_id: Optional[str] = None
    sku_partner_id: Optional[str] = None
    stock_local_name: Optional[str] = None
    amount: Optional[int] = 0
    available_amount: Optional[int] = 0
    price: Optional[float] = None
    active: Optional[bool] = True

class Stock(StockBase):
    id: int
    sku_stock_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class SkuMarketplaceBase(BaseModel):
    anymarket_id: Optional[str] = None
    marketplace: Optional[str] = None
    publication_status: Optional[str] = None
    price: Optional[float] = None
    field_title: Optional[str] = None
    field_ean: Optional[str] = None

class SkuMarketplace(SkuMarketplaceBase):
    id: int
    sku_marketplace_key: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True