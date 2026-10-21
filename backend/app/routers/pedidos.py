from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user
from app.security.decorators import requer_papel

router = APIRouter(prefix="/api/pedidos", tags=["pedidos"])


def validar_proprietario_ou_admin(
    pedido: models.Pedido,
    usuario_atual: models.Usuario
) -> bool:
    """Valida se o usuário é o proprietário do pedido ou é admin"""
    return pedido.usuario_criador_id == usuario_atual.id or usuario_atual.papel == models.Papel.ADMIN


def gerar_numero_pedido(db: Session) -> str:
    """Gera número único de pedido com formato PED-YYYY-NNN"""
    ano = datetime.now().year

    ultimo_pedido = (
        db.query(models.Pedido)
        .filter(models.Pedido.numero_pedido.like(f"PED-{ano}-%"))
        .order_by(models.Pedido.id.desc())
        .first()
    )

    if ultimo_pedido:
        numero = int(ultimo_pedido.numero_pedido.split("-")[-1]) + 1
    else:
        numero = 1

    return f"PED-{ano}-{numero:03d}"


@router.post("", response_model=schemas.PedidoRead, status_code=201)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def criar_pedido(
    pedido_data: schemas.PedidoCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Cria um novo pedido"""

    # Validar produtos e calcular valor total
    valor_total = 0
    items_db = []

    for item in pedido_data.items:
        produto = db.query(models.Produto).filter(models.Produto.id == item.produto_id).first()
        if not produto:
            raise HTTPException(status_code=404, detail=f"Produto {item.produto_id} não encontrado")

        subtotal = item.quantidade * produto.preco_varejo
        valor_total += subtotal

        pedido_item = models.PedidoItem(
            produto_id=item.produto_id,
            quantidade=item.quantidade,
            preco_unitario=produto.preco_varejo,
            subtotal=subtotal
        )
        items_db.append(pedido_item)

    # Criar pedido
    numero_pedido = gerar_numero_pedido(db)
    novo_pedido = models.Pedido(
        numero_pedido=numero_pedido,
        usuario_criador_id=current_user.id,  # ← Adiciona owner check
        cliente_nome=pedido_data.cliente_nome,
        cliente_email=pedido_data.cliente_email,
        cliente_telefone=pedido_data.cliente_telefone,
        data_entrega=pedido_data.data_entrega,
        tipo_entrega=pedido_data.tipo_entrega,
        endereco_entrega=pedido_data.endereco_entrega,
        observacoes=pedido_data.observacoes,
        status=models.StatusPedido.PENDENTE,
        valor_total=valor_total,
        items=items_db
    )

    db.add(novo_pedido)
    db.commit()
    db.refresh(novo_pedido)

    return novo_pedido


@router.get("", response_model=list[schemas.PedidoRead])
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def listar_pedidos(
    data_entrega: datetime | None = Query(None),
    status: models.StatusPedido | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista todos os pedidos com filtros opcionais"""
    query = db.query(models.Pedido)

    if data_entrega:
        # Filtrar por dia (de 00:00 a 23:59)
        inicio_dia = data_entrega.replace(hour=0, minute=0, second=0, microsecond=0)
        fim_dia = inicio_dia + timedelta(days=1)
        query = query.filter(
            models.Pedido.data_entrega >= inicio_dia,
            models.Pedido.data_entrega < fim_dia
        )

    if status:
        query = query.filter(models.Pedido.status == status)

    query = query.order_by(models.Pedido.criado_em.desc())
    pedidos = query.offset(skip).limit(limit).all()

    return pedidos


@router.get("/{pedido_id}", response_model=schemas.PedidoRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def obter_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtém detalhes de um pedido"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    return pedido


@router.put("/{pedido_id}", response_model=schemas.PedidoRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_pedido(
    pedido_id: int,
    pedido_update: schemas.PedidoUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza um pedido (apenas se status for pendente)"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # ✅ Owner check: Apenas o criador ou admin podem editar
    if not validar_proprietario_ou_admin(pedido, current_user):
        raise HTTPException(status_code=403, detail="Sem permissão para editar este pedido")

    if pedido.status != models.StatusPedido.PENDENTE:
        raise HTTPException(
            status_code=400,
            detail="Pedido pode ser editado apenas se estiver com status 'pendente'"
        )

    # Atualizar campos
    if pedido_update.cliente_nome:
        pedido.cliente_nome = pedido_update.cliente_nome
    if pedido_update.cliente_email:
        pedido.cliente_email = pedido_update.cliente_email
    if pedido_update.cliente_telefone:
        pedido.cliente_telefone = pedido_update.cliente_telefone
    if pedido_update.observacoes is not None:
        pedido.observacoes = pedido_update.observacoes

    # Se atualizar items, recalcular valor total
    if pedido_update.items is not None:
        # Remover items antigos
        db.query(models.PedidoItem).filter(models.PedidoItem.pedido_id == pedido_id).delete()

        valor_total = 0
        for item_data in pedido_update.items:
            produto = db.query(models.Produto).filter(models.Produto.id == item_data.produto_id).first()
            if not produto:
                raise HTTPException(status_code=404, detail=f"Produto {item_data.produto_id} não encontrado")

            subtotal = item_data.quantidade * produto.preco_varejo
            valor_total += subtotal

            novo_item = models.PedidoItem(
                pedido_id=pedido_id,
                produto_id=item_data.produto_id,
                quantidade=item_data.quantidade,
                preco_unitario=produto.preco_varejo,
                subtotal=subtotal
            )
            db.add(novo_item)

        pedido.valor_total = valor_total

    db.commit()
    db.refresh(pedido)

    return pedido


@router.delete("/{pedido_id}", status_code=204)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def cancelar_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Cancela um pedido (soft delete - marca como cancelado)"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # ✅ Owner check: Apenas o criador ou admin podem cancelar
    if not validar_proprietario_ou_admin(pedido, current_user):
        raise HTTPException(status_code=403, detail="Sem permissão para cancelar este pedido")

    if pedido.status in [models.StatusPedido.ENTREGUE, models.StatusPedido.CANCELADO]:
        raise HTTPException(status_code=400, detail="Pedido não pode ser cancelado")

    pedido.status = models.StatusPedido.CANCELADO
    db.commit()


@router.patch("/{pedido_id}/status", response_model=schemas.PedidoRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE)
def atualizar_status_pedido(
    pedido_id: int,
    status_update: schemas.PedidoStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Atualiza o status de um pedido"""
    pedido = db.query(models.Pedido).filter(models.Pedido.id == pedido_id).first()

    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")

    # ✅ Owner check: Apenas o criador ou admin podem atualizar status
    if not validar_proprietario_ou_admin(pedido, current_user):
        raise HTTPException(status_code=403, detail="Sem permissão para atualizar este pedido")

    # Validar transição de status
    status_map = {
        models.StatusPedido.PENDENTE: [models.StatusPedido.CONFIRMADO, models.StatusPedido.CANCELADO],
        models.StatusPedido.CONFIRMADO: [models.StatusPedido.PRODUCAO, models.StatusPedido.CANCELADO],
        models.StatusPedido.PRODUCAO: [models.StatusPedido.PRONTO],
        models.StatusPedido.PRONTO: [models.StatusPedido.ENTREGUE],
        models.StatusPedido.ENTREGUE: [],
        models.StatusPedido.CANCELADO: [],
    }

    if status_update.status not in status_map.get(pedido.status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Transição inválida: {pedido.status} -> {status_update.status}"
        )

    pedido.status = status_update.status
    db.commit()
    db.refresh(pedido)

    return pedido
