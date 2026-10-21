"""
Utilitários para geração e validação de JWT tokens
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from app.config import settings

# Configurações
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hora
REFRESH_TOKEN_EXPIRE_DAYS = 7


def criar_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um JWT access token

    Args:
        data: Dados para codificar (ex: {"sub": "usuario_id", "papel": "admin"})
        expires_delta: Tempo de expiração customizado

    Returns:
        Token JWT como string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # PyJWT espera timestamp Unix (segundos), não datetime
    to_encode.update({"exp": int(expire.timestamp())})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def validar_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Valida e decodifica um JWT token

    Args:
        token: JWT token como string

    Returns:
        Dicionário com os dados do token, ou None se inválido
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        print(f"[DEBUG] Payload decodificado com sucesso: {payload}")
        return payload
    except jwt.ExpiredSignatureError as e:
        print(f"[DEBUG] Token expirado: {e}")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[DEBUG] Token inválido: {e}")
        return None
    except Exception as e:
        print(f"[DEBUG] Erro desconhecido ao validar token: {type(e).__name__}: {e}")
        return None


def criar_refresh_token(data: Dict[str, Any]) -> str:
    """
    Cria um JWT refresh token (validade maior)

    Args:
        data: Dados para codificar

    Returns:
        Token JWT como string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    # PyJWT espera timestamp Unix (segundos), não datetime
    to_encode.update({"exp": int(expire.timestamp())})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt
