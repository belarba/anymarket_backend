import requests
import time
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class AnymarketClient:
    def __init__(self):
        self.base_url = os.getenv("ANYMARKET_API_BASE_URL")
        self.gumgatoken = os.getenv("ANYMARKET_GUMGATOKEN")
        
        # Rate limiting: 60 requisições por minuto = 1 req/segundo
        self.request_interval = 1.0
        self.last_request_time = 0
        
        # CORREÇÃO: Token vai no HEADER, não nos parâmetros
        self.headers = {
            "gumgaToken": self.gumgatoken,
            "Content-Type": "application/json"
        }
        
        # Parâmetros da URL (sem o token agora)
        self.params = {}
    
    def _wait_for_rate_limit(self):
        """Aguarda o tempo necessário para respeitar o rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_interval:
            sleep_time = self.request_interval - time_since_last_request
            logger.info(f"Rate limiting: aguardando {sleep_time:.2f} segundos")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_products(self, limit: int = 50, offset: int = 0) -> Dict:
        """Busca produtos da API Anymarket"""
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/products"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            # CORREÇÃO: Token vai no header
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 429:
                logger.warning("Rate limit atingido. Aguardando 60 segundos...")
                time.sleep(60)
                response = requests.get(url, headers=self.headers, params=params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar produtos: {e}")
            return {"content": []}
    
    def get_orders(self, limit: int = 50, offset: int = 0) -> Dict:
        """Busca pedidos da API Anymarket"""
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/orders"
            params = {
                "limit": limit,
                "offset": offset,
            }
            
            # CORREÇÃO: Token vai no header
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 429:
                logger.warning("Rate limit atingido. Aguardando 60 segundos...")
                time.sleep(60)
                response = requests.get(url, headers=self.headers, params=params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar pedidos: {e}")
            return {"content": []}
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Busca um produto específico por ID"""
        try:
            self._wait_for_rate_limit()
            
            url = f"{self.base_url}/products/{product_id}"
            
            # CORREÇÃO: Token vai no header
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 429:
                logger.warning("Rate limit atingido. Aguardando 60 segundos...")
                time.sleep(60)
                response = requests.get(url, headers=self.headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar produto {product_id}: {e}")
            return None