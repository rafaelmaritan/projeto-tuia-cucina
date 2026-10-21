"""
Utilitários para hash e verificação de senhas
Usa bcrypt para segurança
"""
from passlib.context import CryptContext

# Configurar contexto de criptografia com bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_senha(senha: str) -> str:
    """Hash a senha usando bcrypt

    bcrypt tem limite de 72 bytes - truncar se necessário
    """
    # Bcrypt limit: 72 bytes
    senha_truncada = senha[:72]
    return pwd_context.hash(senha_truncada)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash

    bcrypt tem limite de 72 bytes - truncar antes de verificar
    """
    # Bcrypt limit: 72 bytes
    senha_truncada = senha[:72]
    return pwd_context.verify(senha_truncada, senha_hash)
