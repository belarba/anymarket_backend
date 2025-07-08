from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    
    # Informações básicas do produto
    title = Column(String)
    description = Column(Text)
    model = Column(String)
    sku = Column(String, index=True)
    partner_id = Column(String)  # ID do parceiro/seller
    
    # Categoria e marca
    category_id = Column(String)
    category_name = Column(String)
    category_path = Column(String)
    brand_id = Column(String)
    brand_name = Column(String)
    brand_partner_id = Column(String)
    
    # Preços e valores
    price = Column(Float)
    cost_price = Column(Float)
    promotional_price = Column(Float)
    price_factor = Column(Float)
    calculated_price = Column(Boolean, default=False)
    definition_price_scope = Column(String)
    
    # Dimensões e peso
    height = Column(Float)
    width = Column(Float)
    length = Column(Float)
    weight = Column(Float)
    
    # Estoque
    stock_quantity = Column(Integer, default=0)
    stock_local_id = Column(String)
    additional_time = Column(Integer, default=0)  # Tempo adicional de processamento
    
    # Informações técnicas
    nbm_code = Column(String)  # Código NBM
    origin_id = Column(String)  # País de origem
    origin_name = Column(String)
    gender = Column(String)  # Masculino, Feminino, Unissex
    
    # Garantia
    warranty_time = Column(Integer)  # Tempo de garantia em meses
    warranty_text = Column(Text)  # Texto da garantia
    
    # URLs e mídia
    video_url = Column(String)
    main_image_url = Column(String)
    
    # Configurações
    active = Column(Boolean, default=True)
    available = Column(Boolean, default=True)
    allow_automatic_sku_marketplace_creation = Column(Boolean, default=False)
    
    # Marketplace
    marketplace_id = Column(String)
    marketplace_status = Column(String)
    marketplace_integration_status = Column(String)
    
    # Dados JSON para estruturas complexas
    characteristics = Column(JSON)  # Lista de características do produto
    images = Column(JSON)  # Lista de imagens do produto
    skus = Column(JSON)  # Lista de SKUs/variações do produto
    variations = Column(JSON)  # Variações disponíveis
    marketplace_data = Column(JSON)  # Dados específicos do marketplace
    category_data = Column(JSON)  # Dados completos da categoria
    brand_data = Column(JSON)  # Dados completos da marca
    
    # SEO e marketing
    meta_title = Column(String)
    meta_description = Column(Text)
    keywords = Column(Text)
    
    # Datas importantes
    launch_date = Column(DateTime)
    last_updated_marketplace = Column(DateTime)
    last_sync_date = Column(DateTime)
    
    # Status de sincronização
    sync_status = Column(String, default="pending")  # pending, synced, error
    sync_error_message = Column(Text)
    last_sync_attempt = Column(DateTime)
    
    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Product(anymarket_id='{self.anymarket_id}', title='{self.title}', price={self.price})>"

class Order(Base):
    __tablename__ = "orders"
    
    # Campos básicos
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    
    # Informações do pedido
    marketplace = Column(String)
    marketplace_order_id = Column(String)  # ID do pedido no marketplace
    status = Column(String)
    order_type = Column(String)  # Normal, Fulfillment, etc.
    
    # Valores financeiros
    total_amount = Column(Float)
    discount_amount = Column(Float, default=0)
    shipping_amount = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    products_amount = Column(Float, default=0)
    
    # Informações do cliente
    customer_name = Column(String)
    customer_email = Column(String)
    customer_phone = Column(String)
    customer_document = Column(String)  # CPF/CNPJ
    customer_birth_date = Column(DateTime)
    customer_gender = Column(String)
    
    # Endereço de entrega
    shipping_address_street = Column(String)
    shipping_address_number = Column(String)
    shipping_address_complement = Column(String)
    shipping_address_neighborhood = Column(String)
    shipping_address_city = Column(String)
    shipping_address_state = Column(String)
    shipping_address_zip_code = Column(String)
    shipping_address_country = Column(String, default="BR")
    
    # Endereço de cobrança
    billing_address_street = Column(String)
    billing_address_number = Column(String)
    billing_address_complement = Column(String)
    billing_address_neighborhood = Column(String)
    billing_address_city = Column(String)
    billing_address_state = Column(String)
    billing_address_zip_code = Column(String)
    billing_address_country = Column(String, default="BR")
    
    # Informações de envio
    shipping_method = Column(String)
    shipping_company = Column(String)
    tracking_number = Column(String)
    tracking_url = Column(String)
    estimated_delivery_date = Column(DateTime)
    shipped_date = Column(DateTime)
    delivered_date = Column(DateTime)
    
    # Informações de pagamento
    payment_method = Column(String)
    payment_status = Column(String)
    installments = Column(Integer, default=1)
    
    # Nota fiscal
    invoice_number = Column(String)
    invoice_series = Column(String)
    invoice_access_key = Column(String)
    invoice_date = Column(DateTime)
    invoice_cfop = Column(String)
    
    # Observações e comentários
    customer_comments = Column(Text)
    internal_comments = Column(Text)
    marketplace_comments = Column(Text)
    
    # Informações adicionais
    gift_message = Column(Text)
    is_gift = Column(Boolean, default=False)
    
    # Dados JSON para informações complexas
    items_data = Column(JSON)  # Lista completa dos itens do pedido
    payments_data = Column(JSON)  # Informações detalhadas de pagamento
    shipping_data = Column(JSON)  # Dados completos de envio
    marketplace_data = Column(JSON)  # Dados específicos do marketplace
    
    # Datas importantes
    order_date = Column(DateTime)
    approved_date = Column(DateTime)
    invoiced_date = Column(DateTime)
    canceled_date = Column(DateTime)
    
    # Campos de controle
    is_canceled = Column(Boolean, default=False)
    is_invoiced = Column(Boolean, default=False)
    is_shipped = Column(Boolean, default=False)
    is_delivered = Column(Boolean, default=False)
    
    # Metadados
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Order(anymarket_id='{self.anymarket_id}', status='{self.status}', total_amount={self.total_amount})>"