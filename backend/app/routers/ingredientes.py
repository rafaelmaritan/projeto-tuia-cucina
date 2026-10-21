from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user
from app.security.decorators import requer_papel

router = APIRouter(prefix="/api/ingredientes", tags=["ingredientes"])


@router.post("", response_model=schemas.IngredienteRead, status_code=201)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def criar_ingrediente(
    ingrediente_data: schemas.IngredienteCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Cria um novo ingrediente"""

    # Verificar se ingrediente já existe
    existente = db.query(models.Ingrediente).filter(models.Ingrediente.nome == ingrediente_data.nome).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ingrediente com este nome já existe")

    novo_ingrediente = models.Ingrediente(**ingrediente_data.model_dump())
    db.add(novo_ingrediente)
    db.flush()
    db.add(models.Estoque(
        ingrediente_id=novo_ingrediente.id,
        quantidade=0,
        quantidade_minima=0
    ))
    db.commit()
    db.refresh(novo_ingrediente)

    return novo_ingrediente


@router.get("", response_model=list[schemas.IngredienteRead])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def listar_ingredientes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista todos os ingredientes"""
    ingredientes = db.query(models.Ingrediente).offset(skip).limit(limit).all()
    return ingredientes


@router.get("/{ingrediente_id}", response_model=schemas.IngredienteRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def obter_ingrediente(
    ingrediente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtém detalhes de um ingrediente"""
    ingrediente = db.query(models.Ingrediente).filter(models.Ingrediente.id == ingrediente_id).first()

    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")

    return ingrediente


@router.put("/{ingrediente_id}", response_model=schemas.IngredienteRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_ingrediente(
    ingrediente_id: int,
    ingrediente_update: schemas.IngredienteCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza um ingrediente"""
    ingrediente = db.query(models.Ingrediente).filter(models.Ingrediente.id == ingrediente_id).first()

    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")

    for key, value in ingrediente_update.model_dump().items():
        setattr(ingrediente, key, value)

    db.commit()
    db.refresh(ingrediente)

    return ingrediente


@router.delete("/{ingrediente_id}", status_code=204)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def deletar_ingrediente(
    ingrediente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Deleta um ingrediente"""
    ingrediente = db.query(models.Ingrediente).filter(models.Ingrediente.id == ingrediente_id).first()

    if not ingrediente:
        raise HTTPException(status_code=404, detail="Ingrediente não encontrado")

    db.delete(ingrediente)
    db.commit()


@router.get("/estoque/todos", response_model=list[dict])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def listar_estoque(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista estoque de todos ingredientes"""
    estoques = db.query(models.Estoque).all()

    result = []
    for estoque in estoques:
        result.append({
            "id": estoque.id,
            "ingrediente_id": estoque.ingrediente_id,
            "ingrediente_nome": estoque.ingrediente.nome,
            "quantidade": estoque.quantidade,
            "unidade": estoque.ingrediente.unidade,
            "quantidade_minima": estoque.quantidade_minima,
            "status": "OK" if estoque.quantidade >= estoque.quantidade_minima else "ALERTA",
            "atualizado_em": estoque.atualizado_em
        })

    return result


@router.put("/estoque/{estoque_id}", response_model=schemas.EstoqueRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_estoque(
    estoque_id: int,
    estoque_update: schemas.EstoqueUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza quantidade em estoque"""
    estoque = db.query(models.Estoque).filter(models.Estoque.id == estoque_id).first()

    if not estoque:
        raise HTTPException(status_code=404, detail="Estoque não encontrado")

    estoque.quantidade = estoque_update.quantidade
    db.commit()
    db.refresh(estoque)

    return estoque


@router.get("/calculo-necessario/", response_model=schemas.IngredientesNecessariosRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def calcular_ingredientes_necessarios(
    data: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Calcula ingredientes necessários para uma data específica
    Query param: ?data=2026-03-15T00:00:00
    """

    # Buscar todos os pedidos confirmados para a data
    inicio_dia = data.replace(hour=0, minute=0, second=0, microsecond=0)
    fim_dia = inicio_dia + timedelta(days=1)

    pedidos = db.query(models.Pedido).filter(
        models.Pedido.data_entrega >= inicio_dia,
        models.Pedido.data_entrega < fim_dia,
        models.Pedido.status == models.StatusPedido.CONFIRMADO
    ).all()

    # Acumular ingredientes necessários
    ingredientes_totais = {}

    for pedido in pedidos:
        for item in pedido.items:
            # Buscar receita do produto
            receita = db.query(models.Receita).filter(models.Receita.produto_id == item.produto_id).first()

            if not receita or not receita.quantidade_base:
                continue

            # Para cada ingrediente da receita
            for receita_ing in receita.ingredientes:
                # Calcular quantidade necessária
                # quantidade_necessária = quantidade_pedida × (quantidade_ingrediente / quantidade_base)
                quantidade_necessaria = item.quantidade * (receita_ing.quantidade / receita.quantidade_base)

                ing_id = receita_ing.ingrediente_id

                if ing_id not in ingredientes_totais:
                    ingredientes_totais[ing_id] = {
                        "nome": receita_ing.ingrediente.nome,
                        "quantidade": 0,
                        "unidade": receita_ing.ingrediente.unidade,
                        "ingrediente_id": ing_id
                    }

                ingredientes_totais[ing_id]["quantidade"] += quantidade_necessaria

    # Gerar alertas
    alertas = []
    for ing_id, ing_data in ingredientes_totais.items():
        estoque = db.query(models.Estoque).filter(models.Estoque.ingrediente_id == ing_id).first()

        if estoque:
            if estoque.quantidade < ing_data["quantidade"]:
                alertas.append(
                    schemas.IngredientesAlertaRead(
                        ingrediente_id=ing_id,
                        ingrediente_nome=ing_data["nome"],
                        necessario=ing_data["quantidade"],
                        disponivel=estoque.quantidade,
                        diferenca=ing_data["quantidade"] - estoque.quantidade,
                        unidade=ing_data["unidade"]
                    )
                )

    return schemas.IngredientesNecessariosRead(
        data_entrega=data,
        ingredientes=[
            {
                "id": ing_id,
                "nome": ing_data["nome"],
                "quantidade": ing_data["quantidade"],
                "unidade": ing_data["unidade"]
            }
            for ing_id, ing_data in ingredientes_totais.items()
        ],
        alertas=alertas
    )
