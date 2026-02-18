# Anymarket Backend

Sincroniza dados da API Anymarket (products, orders, sku_marketplaces, transmissions) para PostgreSQL.

## Setup

```bash
python3 -m venv anymarket_env
source anymarket_env/bin/activate
pip install -r requirements.txt
```

Criar `.env`:

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/anymarket_db
ANYMARKET_GUMGATOKEN=seu_token_aqui
ANYMARKET_API_BASE_URL=https://sandbox-api.anymarket.com.br/v2
```

## Uso

```bash
# Interativo (products + orders)
python daily_update.py

# Automatico (products + orders)
python daily_update.py --auto

# Incluir SKU marketplaces
python daily_update.py --auto --sku-marketplaces

# Incluir transmissions
python daily_update.py --auto --transmissions

# Tudo
python daily_update.py --auto --all
```

## Cron

```bash
# Todos os dias as 6h
0 6 * * * cd /caminho/para/projeto && /caminho/para/anymarket_env/bin/python daily_update.py --auto
```

## API (FastAPI)

```bash
uvicorn app.main:app --reload
# http://localhost:8000/docs
```
