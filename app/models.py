from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"
    
    # [Manter a estrutura de produtos como está - não alterada]
    id = Column(Integer, primary_key=True, index=True)
    anymarket_id = Column(String, unique=True, index=True)
    title = Column(String)
    description = Column(Text)
    external_id_product = Column(String)
    category_id = Column(String)
    category_name = Column(String)
    category_path = Column(String)
    brand_id = Column(String)
    brand_name = Column(String)
    brand_reduced_name = Column(String)
    brand_partner_id = Column(String)
    nbm_id = Column(String)
    nbm_description = Column(String)
    origin_id = Column(String)
    origin_description = Column(String)
    model = Column(String)
    video_url = Column(String)
    gender = Column(String)
    warranty_time = Column(Integer)
    warranty_text = Column(Text)
    height = Column(Float)
    width = Column(Float)
    weight = Column(Float)
    length = Column(Float)
    price_factor = Column(Float)
    calculated_price = Column(Boolean, default=False)
    definition_price_scope = Column(String)
    has_variations = Column(Boolean, default=False)
    is_product_active = Column(Boolean, default=True)
    product_type = Column(String)
    allow_automatic_sku_marketplace_creation = Column(Boolean, default=True)
    characteristics = Column(JSON)
    images = Column(JSON)
    skus = Column(JSON)
    sku = Column(String, index=True)
    price = Column(Float)
    stock_quantity = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    main_image_url = Column(String)
    total_images = Column(Integer, default=0)
    total_skus = Column(Integer, default=0)
    min_price = Column(Float)
    max_price = Column(Float)
    total_stock = Column(Integer, default=0)
    sync_status = Column(String, default="pending")
    sync_error_message = Column(Text)
    last_sync_date = Column(DateTime)
    last_sync_attempt = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

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
    
    # ========================================================================
    # ITEMS EXPANDIDOS - Primeiro item do array items_data
    # ========================================================================
    
    # Item Product (items[0].product)
    item_product_id = Column(String)  # items[0].product.id
    item_product_title = Column(String)  # items[0].product.title
    
    # Item SKU (items[0].sku)
    item_sku_id = Column(String)  # items[0].sku.id
    item_sku_title = Column(String)  # items[0].sku.title
    item_sku_partner_id = Column(String)  # items[0].sku.partnerId
    item_sku_ean = Column(String)  # items[0].sku.ean
    
    # Item valores (items[0])
    item_amount = Column(Float)  # items[0].amount
    item_unit = Column(Float)  # items[0].unit
    item_gross = Column(Float)  # items[0].gross
    item_total = Column(Float)  # items[0].total
    item_discount = Column(Float)  # items[0].discount
    item_id_in_marketplace = Column(String)  # items[0].idInMarketPlace
    item_order_item_id = Column(String)  # items[0].orderItemId
    item_free_shipping = Column(Boolean, default=False)  # items[0].freeShipping
    item_is_catalog = Column(Boolean, default=False)  # items[0].isCatalog
    item_id_in_marketplace_catalog_origin = Column(String)  # items[0].idInMarketplaceCatalogOrigin
    
    # Item Shipping (items[0].shippings[0]) - primeiro shipping do primeiro item
    item_shipping_id = Column(String)  # items[0].shippings[0].id
    item_shipping_type = Column(String)  # items[0].shippings[0].shippingtype
    item_shipping_carrier_normalized = Column(String)  # items[0].shippings[0].shippingCarrierNormalized
    item_shipping_carrier_type_normalized = Column(String)  # items[0].shippings[0].shippingCarrierTypeNormalized
    
    # Item Stock (items[0].stocks[0]) - primeiro stock do primeiro item
    item_stock_local_id = Column(String)  # items[0].stocks[0].stockLocalId
    item_stock_amount = Column(Float)  # items[0].stocks[0].amount
    item_stock_name = Column(String)  # items[0].stocks[0].stockName
    
    # Campos derivados dos items
    total_items = Column(Integer, default=0)  # Total de itens no pedido
    total_items_amount = Column(Float, default=0)  # Soma de todos os amounts
    total_items_value = Column(Float, default=0)  # Soma de todos os totals
    
    # ========================================================================
    # PAYMENTS EXPANDIDOS - Primeiro payment do array payments_data
    # ========================================================================
    
    # Payment principal (payments[0])
    payment_method = Column(String)  # payments[0].method
    payment_status = Column(String)  # payments[0].status
    payment_value = Column(Float)  # payments[0].value
    payment_marketplace_id = Column(String)  # payments[0].marketplaceId
    payment_method_normalized = Column(String)  # payments[0].paymentMethodNormalized
    payment_detail_normalized = Column(String)  # payments[0].paymentDetailNormalized
    
    # Campos derivados dos payments
    total_payments = Column(Integer, default=0)  # Total de formas de pagamento
    total_payments_value = Column(Float, default=0)  # Soma de todos os values
    
    # ========================================================================
    # DADOS JSON COMPLETOS (para casos que precisam de todos os itens/payments)
    # ========================================================================
    items_data = Column(JSON)  # Array completo de items
    payments_data = Column(JSON)  # Array completo de payments
    shippings_data = Column(JSON)  # Array de shippings
    stocks_data = Column(JSON)  # Array de stocks
    metadata_extra = Column(JSON)  # Metadata completo
    
    # Metadados do sistema
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Order(anymarket_id='{self.anymarket_id}', status='{self.status}', total={self.total})>"