from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import sessionmaker, session
from app.config import settings

database_url = make_url(settings.DATABASE_URL)
if database_url.drivername in {"postgres", "postgresql"}:
    database_url = database_url.set(drivername="postgresql+psycopg")

# Criar engine
engine = create_engine(
    database_url,
    echo=settings.SQLALCHEMY_ECHO,
    connect_args={"check_same_thread": False} if database_url.get_backend_name() == "sqlite" else {}
)

# Criar factory de sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency para injetar a sessão do banco nos endpoints"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
