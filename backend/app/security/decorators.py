"""
Decoradores de segurança para verificação de papéis/permissões
"""
from functools import wraps
from fastapi import Depends, HTTPException, status
from app.security.jwt import validar_token
from app.database import get_db
from app import models
from sqlalchemy.orm import Session


def requer_papel(*papeis_permitidos):
    """
    Decorator para verificar se o usuário tem um dos papéis permitidos

    Uso:
        @app.get("/admin-only")
        @requer_papel(models.Papel.ADMIN)
        def admin_endpoint(current_user = Depends(get_current_user)):
            return {"mensagem": "Apenas admin"}

        @app.get("/gerente-ou-admin")
        @requer_papel(models.Papel.GERENTE, models.Papel.ADMIN)
        def gerente_endpoint(current_user = Depends(get_current_user)):
            return {"mensagem": "Gerente ou Admin"}

    Args:
        *papeis_permitidos: Um ou mais papéis da enum Papel que são permitidos
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extrair usuário do kwargs (deve vir do Depends)
            current_user = kwargs.get('current_user')

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Não autenticado"
                )

            if current_user.papel not in papeis_permitidos:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Papel '{current_user.papel}' não tem permissão para acessar este recurso"
                )

            return func(*args, **kwargs)

        return wrapper
    return decorator


def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)):
    """
    Dependência para extrair e validar o usuário atual do token JWT

    Uso como Depends em endpoints:
        @app.get("/me")
        def get_me(current_user = Depends(get_current_user)):
            return current_user
    """
    # Este é um exemplo base - normalmente implementado no auth.py
    # Mantém compatibilidade com routers que precisam desta função
    pass
