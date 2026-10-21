from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import pedidos, produtos, receitas, ingredientes, dashboard, estoque, auth
from app.seed import seed_database

# Criar tabelas no banco
Base.metadata.create_all(bind=engine)

# Seed dos dados iniciais
try:
    seed_database()
except Exception as e:
    if settings.ENVIRONMENT.lower() == "production":
        raise
    print(f"Aviso: Seed falhou - {e}")

# Inicializar aplicação
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="API para gestão de pedidos e receitas da Tuia Cucina"
)

# CORS - Permitir credenciais (cookies)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.CORS_ORIGINS.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(auth.router)
app.include_router(pedidos.router)
app.include_router(produtos.router)
app.include_router(receitas.router)
app.include_router(ingredientes.router)
app.include_router(estoque.router)
app.include_router(dashboard.router)


@app.get("/")
def root():
    """Health check"""
    return {
        "message": "Tuia Cucina API",
        "version": settings.API_VERSION,
        "status": "healthy"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
