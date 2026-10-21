from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user
from app.security.decorators import requer_papel

router = APIRouter(prefix="/api/receitas", tags=["receitas"])


@router.post("", response_model=schemas.ReceitaRead, status_code=201)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def criar_receita(
    receita_data: schemas.ReceitaCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Cria uma nova receita para um produto"""

    # Verificar se produto existe
    produto = db.query(models.Produto).filter(models.Produto.id == receita_data.produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Verificar se receita já existe para este produto
    existente = db.query(models.Receita).filter(models.Receita.produto_id == receita_data.produto_id).first()
    if existente:
        raise HTTPException(status_code=400, detail="Receita já existe para este produto")

    nova_receita = models.Receita(
        produto_id=receita_data.produto_id,
        quantidade_base=receita_data.quantidade_base,
        tempo_fermentacao_horas=receita_data.tempo_fermentacao_horas,
        tempo_assamento_minutos=receita_data.tempo_assamento_minutos,
        instrucoes=receita_data.instrucoes
    )

    # Adicionar ingredientes
    for ing_data in receita_data.ingredientes:
        ingrediente = db.query(models.Ingrediente).filter(models.Ingrediente.id == ing_data.ingrediente_id).first()
        if not ingrediente:
            raise HTTPException(status_code=404, detail=f"Ingrediente {ing_data.ingrediente_id} não encontrado")

        receita_ingrediente = models.ReceitaIngrediente(
            ingrediente_id=ing_data.ingrediente_id,
            quantidade=ing_data.quantidade
        )
        nova_receita.ingredientes.append(receita_ingrediente)

    db.add(nova_receita)
    db.commit()
    db.refresh(nova_receita)

    return nova_receita


@router.get("", response_model=list[schemas.ReceitaRead])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE, models.Papel.PADEIRO)
def listar_receitas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista todas as receitas"""
    receitas = db.query(models.Receita).offset(skip).limit(limit).all()
    return receitas


@router.get("/{receita_id}", response_model=schemas.ReceitaRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE, models.Papel.PADEIRO)
def obter_receita(
    receita_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtém detalhes de uma receita"""
    receita = db.query(models.Receita).filter(models.Receita.id == receita_id).first()

    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    return receita


@router.put("/{receita_id}", response_model=schemas.ReceitaRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_receita(
    receita_id: int,
    receita_update: schemas.ReceitaUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza uma receita"""
    receita = db.query(models.Receita).filter(models.Receita.id == receita_id).first()

    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    # Atualizar campos simples
    if receita_update.nome is not None:
        receita.nome = receita_update.nome
    if receita_update.quantidade_base is not None:
        receita.quantidade_base = receita_update.quantidade_base
    if receita_update.tempo_fermentacao_horas is not None:
        receita.tempo_fermentacao_horas = receita_update.tempo_fermentacao_horas
    if receita_update.tempo_assamento_minutos is not None:
        receita.tempo_assamento_minutos = receita_update.tempo_assamento_minutos
    if receita_update.instrucoes is not None:
        receita.instrucoes = receita_update.instrucoes

    # Atualizar ingredientes
    if receita_update.ingredientes is not None:
        # Remover ingredientes antigos
        db.query(models.ReceitaIngrediente).filter(models.ReceitaIngrediente.receita_id == receita_id).delete()

        # Adicionar novos
        for ing_data in receita_update.ingredientes:
            ingrediente = db.query(models.Ingrediente).filter(models.Ingrediente.id == ing_data.ingrediente_id).first()
            if not ingrediente:
                raise HTTPException(status_code=404, detail=f"Ingrediente {ing_data.ingrediente_id} não encontrado")

            receita_ingrediente = models.ReceitaIngrediente(
                receita_id=receita_id,
                ingrediente_id=ing_data.ingrediente_id,
                quantidade=ing_data.quantidade
            )
            db.add(receita_ingrediente)

    db.commit()
    db.refresh(receita)

    return receita


@router.delete("/{receita_id}", status_code=204)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def deletar_receita(
    receita_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Deleta uma receita"""
    receita = db.query(models.Receita).filter(models.Receita.id == receita_id).first()

    if not receita:
        raise HTTPException(status_code=404, detail="Receita não encontrada")

    db.delete(receita)
    db.commit()
