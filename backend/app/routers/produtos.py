from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user
from app.security.decorators import requer_papel

router = APIRouter(prefix="/api/produtos", tags=["produtos"])


@router.post("", response_model=schemas.ProdutoRead, status_code=201)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def criar_produto(
    produto_data: schemas.ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Cria um novo produto"""

    # Verificar se produto já existe
    existente = db.query(models.Produto).filter(models.Produto.nome == produto_data.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Produto com este nome já existe")

    novo_produto = models.Produto(**produto_data.model_dump())
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)

    return novo_produto


@router.get("", response_model=list[schemas.ProdutoRead])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def listar_produtos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista todos os produtos"""
    produtos = db.query(models.Produto).offset(skip).limit(limit).all()
    return produtos


@router.get("/{produto_id}", response_model=schemas.ProdutoRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def obter_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtém detalhes de um produto"""
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    return produto


@router.put("/{produto_id}", response_model=schemas.ProdutoRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_produto(
    produto_id: int,
    produto_update: schemas.ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza um produto"""
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    for key, value in produto_update.model_dump().items():
        setattr(produto, key, value)

    db.commit()
    db.refresh(produto)

    return produto


@router.delete("/{produto_id}", status_code=204)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def deletar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Deleta um produto"""
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()

    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    db.delete(produto)
    db.commit()
