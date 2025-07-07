# Anymarket Backend

Backend em Python/FastAPI para sincronização de dados da API Anymarket com banco PostgreSQL.

## 🚀 Como Iniciar

### 1. **Pré-requisitos**
- Python 3.11+
- PostgreSQL (ou SQLite para desenvolvimento)
- Token gumgaToken da Anymarket

### 2. **Instalação**

```bash
# Clonar repositório
git clone <url-do-repo>
cd anymarket_backend

# Criar ambiente virtual
python3 -m venv anymarket_env
source anymarket_env/bin/activate  # Linux/Mac
# anymarket_env\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. **Configuração**

Crie um arquivo `.env` na raiz do projeto:

```env
# Banco de dados
DATABASE_URL=postgresql://usuario:senha@localhost:5432/anymarket_db
# ou para SQLite: DATABASE_URL=sqlite:///./anymarket.db

# API Anymarket
ANYMARKET_GUMGATOKEN=seu_token_aqui
ANYMARKET_API_BASE_URL=https://sandbox-api.anymarket.com.br/v2
```

### 4. **Executar Aplicação**

```bash
# Ativar ambiente virtual (se não estiver ativo)
source anymarket_env/bin/activate

# Executar aplicação
python -m app.main

# Ou com uvicorn
uvicorn app.main:app --reload
```

A aplicação estará rodando em: **http://localhost:8000**

## 📋 Endpoints Disponíveis

### **Interface e Documentação**
- `GET /` - Página inicial
- `GET /docs` - Documentação automática da API (Swagger)
- `GET /redoc` - Documentação alternativa (ReDoc)

### **Sincronização de Dados**
- `POST /sync/products` - Sincroniza todos os produtos da Anymarket
- `POST /sync/orders` - Sincroniza todos os pedidos da Anymarket

### **Consulta de Dados**
- `GET /products` - Lista produtos do banco local
  - Query params: `skip=0&limit=100`
- `GET /orders` - Lista pedidos do banco local
  - Query params: `skip=0&limit=100`

## 🔧 Exemplos de Uso

### **Sincronizar Produtos**
```bash
curl -X POST http://localhost:8000/sync/products
```

### **Sincronizar Pedidos**
```bash
curl -X POST http://localhost:8000/sync/orders
```

### **Listar Produtos**
```bash
# Primeiros 10 produtos
curl "http://localhost:8000/products?limit=10"

# Produtos 20-30
curl "http://localhost:8000/products?skip=20&limit=10"
```

### **Listar Pedidos**
```bash
# Primeiros 10 pedidos
curl "http://localhost:8000/orders?limit=10"
```

## ⚙️ Configurações Importantes

### **Rate Limiting**
- A API da Anymarket tem limite de **60 requisições por minuto**
- O sistema automaticamente aguarda 1 segundo entre requisições
- Retry automático em caso de rate limit (HTTP 429)

### **Sincronização**
- Todas as sincronizações rodam em **background**
- Produtos e pedidos são criados ou atualizados (upsert)
- Logs detalhados no console

### **Banco de Dados**
- Tabelas são criadas automaticamente na primeira execução
- Suporte para PostgreSQL e SQLite
- Campos `created_at` e `updated_at` automáticos

## 📊 Estrutura dos Dados

### **Produtos**
```json
{
  "id": 1,
  "anymarket_id": "3895801",
  "title": "Nome do Produto",
  "description": "Descrição detalhada",
  "price": 99.99,
  "brand": "Marca",
  "model": "Modelo",
  "category": "Categoria",
  "sku": "SKU123",
  "stock_quantity": 10,
  "active": true,
  "created_at": "2025-01-07T15:30:00Z",
  "updated_at": "2025-01-07T15:30:00Z"
}
```

### **Pedidos**
```json
{
  "id": 1,
  "anymarket_id": "12345",
  "marketplace": "Mercado Livre",
  "status": "APROVADO",
  "total_amount": 299.90,
  "customer_name": "João Silva",
  "customer_email": "joao@email.com",
  "order_date": "2025-01-07T15:30:00Z",
  "created_at": "2025-01-07T15:30:00Z",
  "updated_at": "2025-01-07T15:30:00Z"
}
```

## 🛠️ Desenvolvimento

### **Logs**
A aplicação gera logs detalhados:
```
INFO - Rate limiting: aguardando 1.00 segundos
INFO - Buscando produtos: offset 0, limit 50
INFO - Total de produtos coletados: 50
```

### **Estrutura do Projeto**
```
anymarket_backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicação principal
│   ├── models.py            # Modelos do banco
│   ├── schemas.py           # Schemas Pydantic
│   ├── database.py          # Configuração do banco
│   └── anymarket_client.py  # Cliente da API
├── .env                     # Variáveis de ambiente (não versionado)
├── .gitignore
├── requirements.txt
└── README.md
```

## 🚨 Troubleshooting

### **Erro 401 Unauthorized**
- Verifique se o `ANYMARKET_GUMGATOKEN` está correto
- Confirme se está usando a URL correta (sandbox vs produção)

### **Erro de Banco de Dados**
- Verifique se o PostgreSQL está rodando
- Confirme as credenciais no `.env`
- Para desenvolvimento, use SQLite: `DATABASE_URL=sqlite:///./anymarket.db`

### **Rate Limit**
- O sistema já trata automaticamente
- Para muitos dados, a sincronização pode demorar

## 📝 Notas

- As sincronizações rodam em background e não bloqueiam a API
- Dados são atualizados automaticamente (upsert)
- Suporte a sandbox e produção da Anymarket
- Rate limiting respeitado automaticamente

## 🔗 Links Úteis

- [Documentação Anymarket API](https://developers.anymarket.com.br/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)