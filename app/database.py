from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não encontrada nas variáveis de ambiente")

# Configurações específicas para diferentes tipos de banco
if DATABASE_URL.startswith("sqlite"):
    # Para SQLite local (desenvolvimento)
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
elif DATABASE_URL.startswith("postgresql://"):
    # Para PostgreSQL/Neon - corrigir URL se necessário
    corrected_url = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Configurações otimizadas para Neon
    engine = create_engine(
        corrected_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False  # Mude para True se quiser ver as queries SQL
    )
else:
    # Para URLs já formatadas corretamente
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency para obter sessão do banco"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection():
    """Testa a conexão com o banco de dados"""
    try:
        with engine.connect() as connection:
            logger.info("✅ Conexão com banco de dados estabelecida com sucesso")
            return True
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com banco de dados: {e}")
        return False