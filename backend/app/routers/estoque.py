from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user
from app.security.decorators import requer_papel

router = APIRouter(prefix="/api/estoque", tags=["estoque"])


@router.get("/alertas", response_model=list[dict])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def obter_alertas_estoque(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Retorna ingredientes com estoque baixo ou crítico"""
    estoques = db.query(models.Estoque).all()

    alertas = []
    for estoque in estoques:
        if estoque.quantidade <= estoque.quantidade_minima:
            status = "crítico" if estoque.quantidade == 0 else "baixo"
            alertas.append({
                "id": estoque.id,
                "ingrediente_id": estoque.ingrediente_id,
                "ingrediente_nome": estoque.ingrediente.nome,
                "unidade": estoque.ingrediente.unidade,
                "quantidade_atual": estoque.quantidade,
                "quantidade_minima": estoque.quantidade_minima,
                "status": status,
            })

    return sorted(alertas, key=lambda x: x["quantidade_atual"])


@router.get("/by-ingrediente/{ingrediente_id}", response_model=schemas.EstoqueComMovimentos)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def obter_estoque_ingrediente(
    ingrediente_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtém estoque de um ingrediente com histórico de movimentos"""
    estoque = (
        db.query(models.Estoque)
        .filter(models.Estoque.ingrediente_id == ingrediente_id)
        .first()
    )

    if not estoque:
        raise HTTPException(status_code=404, detail="Estoque não encontrado para este ingrediente")

    return estoque


@router.get("", response_model=list[schemas.EstoqueRead])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def listar_estoque(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista estoque de todos os ingredientes"""
    estoques = db.query(models.Estoque).offset(skip).limit(limit).all()
    return estoques


@router.post("/{estoque_id}/movimento", response_model=schemas.EstoqueComMovimentos)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def registrar_movimento(
    estoque_id: int,
    movimento_data: schemas.EstoqueMovimentoBase,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Registra entrada, saída ou ajuste de estoque"""
    estoque = db.query(models.Estoque).filter(models.Estoque.id == estoque_id).first()

    if not estoque:
        raise HTTPException(status_code=404, detail="Estoque não encontrado")

    # Validar tipo de movimento
    tipos_validos = ["entrada", "saída", "ajuste"]
    if movimento_data.tipo not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Use: {', '.join(tipos_validos)}")

    # Registrar movimento
    novo_movimento = models.EstoqueMovimento(
        estoque_id=estoque_id,
        tipo=movimento_data.tipo,
        quantidade=movimento_data.quantidade,
        observacao=movimento_data.observacao,
    )
    db.add(novo_movimento)

    # Atualizar quantidade em estoque
    if movimento_data.tipo == "entrada":
        estoque.quantidade += movimento_data.quantidade
    elif movimento_data.tipo == "saída":
        if estoque.quantidade < movimento_data.quantidade:
            raise HTTPException(
                status_code=400,
                detail=f"Quantidade insuficiente. Disponível: {estoque.quantidade}"
            )
        estoque.quantidade -= movimento_data.quantidade
    elif movimento_data.tipo == "ajuste":
        estoque.quantidade = movimento_data.quantidade

    db.commit()
    db.refresh(estoque)

    return estoque


@router.get("/{estoque_id}/historico", response_model=list[schemas.EstoqueMovimentoRead])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def obter_historico_movimentos(
    estoque_id: int,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtém histórico de movimentos de um estoque"""
    estoque = db.query(models.Estoque).filter(models.Estoque.id == estoque_id).first()

    if not estoque:
        raise HTTPException(status_code=404, detail="Estoque não encontrado")

    movimentos = (
        db.query(models.EstoqueMovimento)
        .filter(models.EstoqueMovimento.estoque_id == estoque_id)
        .order_by(models.EstoqueMovimento.criado_em.desc())
        .limit(limit)
        .all()
    )

    return movimentos


@router.put("/{estoque_id}/quantidade-minima", response_model=schemas.EstoqueRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_quantidade_minima(
    estoque_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza a quantidade mínima de um ingrediente"""
    estoque = db.query(models.Estoque).filter(models.Estoque.id == estoque_id).first()

    if not estoque:
        raise HTTPException(status_code=404, detail="Estoque não encontrado")

    if "quantidade_minima" not in data:
        raise HTTPException(status_code=400, detail="Campo 'quantidade_minima' obrigatório")

    estoque.quantidade_minima = data["quantidade_minima"]
    db.commit()
    db.refresh(estoque)

    return estoque
