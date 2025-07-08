from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class ProductBase(BaseModel):
    # Informações básicas
    title: str
    description: Optional[str] = None
    model: Optional[str] = None
    sku: Optional[str] = None
    partner_id: Optional[str] = None
    
    # Categoria e marca
    category_id: Optional[str] = None
    category_name: Optional[str] = None
    category_path: Optional[str] = None
    brand_id: Optional[str] = None
    brand_name: Optional[str] = None
    brand_partner_id: Optional[str] = None
    
    # Preços
    price: float = 0
    cost_price: Optional[float] = None
    promotional_price: Optional[float] = None
    price_factor: Optional[float] = None
    calculated_price: Optional[bool] = False
    definition_price_scope: Optional[str] = None
    
    # Dimensões e peso
    height: Optional[float] = None
    width: Optional[float] = None
    length: Optional[float] = None
    weight: Optional[float] = None
    
    # Estoque
    stock_quantity: Optional[int] = 0
    stock_local_id: Optional[str] = None
    additional_time: Optional[int] = 0
    
    # Informações técnicas
    nbm_code: Optional[str] = None
    origin_id: Optional[str] = None
    origin_name: Optional[str] = None
    gender: Optional[str] = None
    
    # Garantia
    warranty_time: Optional[int] = None
    warranty_text: Optional[str] = None
    
    # URLs e mídia
    video_url: Optional[str] = None
    main_image_url: Optional[str] = None
    
    # Status
    active: Optional[bool] = True
    available: Optional[bool] = True
    allow_automatic_sku_marketplace_creation: Optional[bool] = False
    
    # Marketplace
    marketplace_id: Optional[str] = None
    marketplace_status: Optional[str] = None
    marketplace_integration_status: Optional[str] = None
    
    # Dados JSON
    characteristics: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[Dict[str, Any]]] = None
    skus: Optional[List[Dict[str, Any]]] = None
    variations: Optional[Dict[str, Any]] = None
    marketplace_data: Optional[Dict[str, Any]] = None
    category_data: Optional[Dict[str, Any]] = None
    brand_data: Optional[Dict[str, Any]] = None
    
    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    keywords: Optional[str] = None
    
    # Datas
    launch_date: Optional[datetime] = None
    last_updated_marketplace: Optional[datetime] = None
    last_sync_date: Optional[datetime] = None
    
    # Sincronização
    sync_status: Optional[str] = "pending"
    sync_error_message: Optional[str] = None
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

# Schema simplificado para listagens
class ProductSummary(BaseModel):
    id: int
    anymarket_id: str
    title: str
    sku: Optional[str]
    brand_name: Optional[str]
    category_name: Optional[str]
    price: float
    stock_quantity: Optional[int]
    active: Optional[bool]
    sync_status: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# Schemas para Orders (mantidos iguais)
class OrderBase(BaseModel):
    # Informações básicas
    marketplace: Optional[str] = None
    marketplace_order_id: Optional[str] = None
    status: Optional[str] = None
    order_type: Optional[str] = None
    
    # Valores financeiros
    total_amount: float = 0
    discount_amount: Optional[float] = 0
    shipping_amount: Optional[float] = 0
    tax_amount: Optional[float] = 0
    products_amount: Optional[float] = 0
    
    # Informações do cliente
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_document: Optional[str] = None
    customer_birth_date: Optional[datetime] = None
    customer_gender: Optional[str] = None
    
    # Endereço de entrega
    shipping_address_street: Optional[str] = None
    shipping_address_number: Optional[str] = None
    shipping_address_complement: Optional[str] = None
    shipping_address_neighborhood: Optional[str] = None
    shipping_address_city: Optional[str] = None
    shipping_address_state: Optional[str] = None
    shipping_address_zip_code: Optional[str] = None
    shipping_address_country: Optional[str] = "BR"
    
    # Endereço de cobrança
    billing_address_street: Optional[str] = None
    billing_address_number: Optional[str] = None
    billing_address_complement: Optional[str] = None
    billing_address_neighborhood: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_state: Optional[str] = None
    billing_address_zip_code: Optional[str] = None
    billing_address_country: Optional[str] = "BR"
    
    # Informações de envio
    shipping_method: Optional[str] = None
    shipping_company: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    estimated_delivery_date: Optional[datetime] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    
    # Informações de pagamento
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    installments: Optional[int] = 1
    
    # Nota fiscal
    invoice_number: Optional[str] = None
    invoice_series: Optional[str] = None
    invoice_access_key: Optional[str] = None
    invoice_date: Optional[datetime] = None
    invoice_cfop: Optional[str] = None
    
    # Observações
    customer_comments: Optional[str] = None
    internal_comments: Optional[str] = None
    marketplace_comments: Optional[str] = None
    gift_message: Optional[str] = None
    is_gift: Optional[bool] = False
    
    # Dados JSON
    items_data: Optional[Dict[str, Any]] = None
    payments_data: Optional[Dict[str, Any]] = None
    shipping_data: Optional[Dict[str, Any]] = None
    marketplace_data: Optional[Dict[str, Any]] = None
    
    # Datas importantes
    order_date: Optional[datetime] = None
    approved_date: Optional[datetime] = None
    invoiced_date: Optional[datetime] = None
    canceled_date: Optional[datetime] = None
    
    # Status flags
    is_canceled: Optional[bool] = False
    is_invoiced: Optional[bool] = False
    is_shipped: Optional[bool] = False
    is_delivered: Optional[bool] = False

class OrderCreate(OrderBase):
    anymarket_id: str

class Order(OrderBase):
    id: int
    anymarket_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema específico para resposta simplificada
class OrderSummary(BaseModel):
    id: int
    anymarket_id: str
    marketplace: Optional[str]
    status: Optional[str]
    total_amount: float
    customer_name: Optional[str]
    order_date: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True