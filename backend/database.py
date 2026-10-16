import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Configuração da URL de conexão (MySQL por padrão)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "mysql+pymysql://root:root@localhost:3306/gincana_jenpex"
)

# Suporte didático: se for sqlite para testes rápidos sem mysql
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Conexão MySQL com pooling para concorrência
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    Função geradora de sessão do banco para injeção de dependência no FastAPI.
    Garante o fechamento automático da conexão após cada requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
