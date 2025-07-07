import requests
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

class AnymarketClient:
    def __init__(self):
        self.base_url = os.getenv("ANYMARKET_API_BASE_URL")
        self.gumgatoken = os.getenv("ANYMARKET_GUMGATOKEN")

        # A API da Anymarket usa gumgatoken como parâmetro na URL
        self.params = {
          "gumgatoken": self.gumgatoken
        } 

    def get_products(self, limit: int = 50, offset: int = 0) -> Dict:
        """Busca produtos da API Anymarket"""
        try:
            url = f"{self.base_url}/products"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar produtos: {e}")
            return {"content": []}
    
    def get_orders(self, limit: int = 50, offset: int = 0) -> Dict:
        """Busca pedidos da API Anymarket"""
        try:
            url = f"{self.base_url}/orders"
            params = {
                "limit": limit,
                "offset": offset
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar pedidos: {e}")
            return {"content": []}
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Busca um produto específico por ID"""
        try:
            url = f"{self.base_url}/products/{product_id}"
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar produto {product_id}: {e}")
            return None