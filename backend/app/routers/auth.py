"""
Router para autenticação (login, logout, refresh token)
Usa httpOnly cookies para maior segurança contra XSS
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Response, Cookie, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app import models
from app.config import Settings
from app.security.password import hash_senha, verificar_senha
from app.security.jwt import criar_access_token, criar_refresh_token, validar_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])
settings = Settings()  # Instância global de configurações


# ==================== HELPERS ====================
def is_https_request(request: Request) -> bool:
    """
    Detecta se a requisição é HTTPS verificando:
    1. Header X-Forwarded-Proto (Railway/proxy reverso)
    2. Esquema da URL
    3. Variável de ambiente ENVIRONMENT
    """
    # Verificar header X-Forwarded-Proto (Railway envia isso)
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    if forwarded_proto == "https":
        print(f"[DEBUG] HTTPS detectado via X-Forwarded-Proto")
        return True

    # Verificar esquema da URL
    if request.url.scheme == "https":
        print(f"[DEBUG] HTTPS detectado via URL scheme")
        return True

    # Verificar variável de ambiente
    if settings.ENVIRONMENT == "production":
        print(f"[DEBUG] HTTPS detectado via ENVIRONMENT=production")
        return True

    print(f"[DEBUG] Usando HTTP (desenvolvimento)")
    return False


# ==================== SCHEMAS ====================
class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    papel: str
    nome: str

    class Config:
        from_attributes = True


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str


# ==================== DEPENDÊNCIAS ====================
def get_current_user(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
) -> models.Usuario:
    """
    Dependência para extrair e validar o usuário atual do token JWT
    Suporte a dois métodos:
    1. Header: Authorization: Bearer <token> (compatibilidade)
    2. Cookie: access_token (novo - httpOnly) ✅

    Uso:
        @app.get("/protected")
        def rota_protegida(current_user: Usuario = Depends(get_current_user)):
            ...
    """
    token = None

    # Tentar extrair do header Authorization
    if authorization:
        try:
            parts = authorization.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                print(f"[DEBUG] Token extraído do header Authorization")
        except (ValueError, IndexError):
            pass

    # Se não encontrou no header, tentar do cookie
    if not token and access_token:
        token = access_token
        print(f"[DEBUG] Token extraído do cookie")

    if not token:
        print(f"[DEBUG] Nenhum token fornecido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não fornecido"
        )

    # Validar token
    payload = validar_token(token)
    if not payload:
        print(f"[DEBUG] Token inválido ou expirado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    # Buscar usuário no banco
    usuario_id = int(payload.get("sub"))
    usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

    if not usuario or not usuario.ativo:
        print(f"[DEBUG] Usuário {usuario_id} não encontrado ou inativo")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )

    print(f"[DEBUG] Usuário autenticado: {usuario.email}")
    return usuario


# ==================== ENDPOINTS ====================
@router.post("/login", response_model=LoginResponse)
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Faz login com email/senha e retorna tokens como cookies httpOnly

    Exemplo:
        POST /api/auth/login
        {
            "email": "admin@tuia.com",
            "senha": "admin123"
        }
    """
    # Buscar usuário no banco
    usuario = db.query(models.Usuario).filter(
        models.Usuario.email == login_data.email
    ).first()

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )

    # Validar senha
    if not verificar_senha(login_data.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos"
        )

    # Verificar se usuário está ativo
    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário desativado"
        )

    # Gerar tokens
    access_token = criar_access_token(data={
        "sub": str(usuario.id),
        "email": usuario.email,
        "papel": usuario.papel
    })

    refresh_token = criar_refresh_token(data={
        "sub": str(usuario.id),
        "email": usuario.email,
        "tipo": "refresh"
    })

    # ✅ Configurar cookies httpOnly (seguro contra XSS)
    # Em desenvolvimento (HTTP), usar secure=False
    # Em produção (HTTPS), usar secure=True
    # Detecta HTTPS automaticamente via X-Forwarded-Proto (Railway)
    is_secure = is_https_request(request)

    # Criar resposta JSON que preserve os cookies
    response_data = {
        "access_token": "cookie",  # Apenas para compatibilidade com schema
        "refresh_token": None,
        "papel": usuario.papel.value if hasattr(usuario.papel, 'value') else str(usuario.papel),
        "nome": usuario.nome
    }

    response = JSONResponse(content=response_data, status_code=200)

    # Setear cookies na resposta
    # Para cookies cross-domain (frontend em pages.dev, backend em railway.app):
    # - SameSite=None permite envio em requisições cross-site
    # - Secure=True é OBRIGATÓRIO quando SameSite=None
    samesite_value = "None" if is_secure else "Lax"

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,      # Não acessível via JavaScript
        secure=is_secure,   # HTTPS em produção (Railway) ou local
        samesite=samesite_value,  # None em produção, Lax em dev
        max_age=3600,       # 1 hora (mesmo que JWT)
        path="/"            # Disponível em todo o domínio
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite=samesite_value,  # None em produção, Lax em dev
        max_age=604800,     # 7 dias
        path="/"
    )

    # Retornar resposta com cookies inclusos
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    request: Request,
    refresh_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Renova o access token usando um refresh token do cookie

    O refresh_token é lido automaticamente do cookie httpOnly ✅

    Exemplo:
        POST /api/auth/refresh
        (Cookie: refresh_token=eyJ0eXAiOiJKV1QiLCJhbGc...)
    """
    if not refresh_token:
        print(f"[DEBUG] Refresh token não encontrado no cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token não encontrado"
        )

    print(f"[DEBUG] Refresh token recebido, validando...")
    # Validar refresh token
    payload = validar_token(refresh_token)
    if not payload or payload.get("tipo") != "refresh":
        print(f"[DEBUG] Refresh token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )

    # Buscar usuário
    usuario_id = payload.get("sub")
    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id
    ).first()

    if not usuario or not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )

    # Gerar novo access token
    new_access_token = criar_access_token(data={
        "sub": usuario.id,
        "email": usuario.email,
        "papel": usuario.papel
    })

    # ✅ Retornar novo access_token como cookie também
    is_secure = is_https_request(request)

    response_data = {
        "access_token": "cookie"  # Apenas para compatibilidade
    }

    response = JSONResponse(content=response_data, status_code=200)
    samesite_value = "None" if is_secure else "Lax"
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=is_secure,
        samesite=samesite_value,
        max_age=3600
    )

    print(f"[DEBUG] Novo access token criado para {usuario.email}")
    return response


@router.post("/logout")
def logout(response: Response):
    """
    Logout - Limpa os cookies httpOnly

    ✅ Não exige autenticação pois o objetivo é apenas remover os cookies
    Em uma implementação real, você poderia adicionar o token a um blacklist
    """
    # ✅ Limpar cookies httpOnly
    response.delete_cookie(key="access_token", path="/", domain=None)
    response.delete_cookie(key="refresh_token", path="/", domain=None)

    return {"message": "Logout realizado com sucesso"}


@router.get("/me")
def obter_usuario_atual(current_user: models.Usuario = Depends(get_current_user)):
    """
    Retorna os dados do usuário autenticado
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "nome": current_user.nome,
        "papel": current_user.papel.value if hasattr(current_user.papel, 'value') else str(current_user.papel),
        "ativo": current_user.ativo
    }
