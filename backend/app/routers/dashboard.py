from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app import models, schemas
from app.routers.auth import get_current_user
from app.security.decorators import requer_papel

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/home", response_model=schemas.DashboardHomeRead)
@requer_papel(models.Papel.ADMIN, models.Papel.GERENTE, models.Papel.PADEIRO)
def dashboard_home(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Retorna dados da home do dashboard"""

    # Próximas entregas (próximos 7 dias)
    hoje = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    fim_semana = hoje + timedelta(days=7)

    proximas_entregas_query = (
        db.query(
            models.Pedido.data_entrega,
            func.count(models.Pedido.id).label("total_pedidos"),
            func.max(models.Pedido.status).label("status")
        )
        .filter(
            models.Pedido.data_entrega >= hoje,
            models.Pedido.data_entrega < fim_semana,
            models.Pedido.status != models.StatusPedido.CANCELADO
        )
        .group_by(models.Pedido.data_entrega)
        .order_by(models.Pedido.data_entrega)
        .all()
    )

    proximas_entregas = [
        schemas.ProximaEntregaRead(
            data=row[0],
            total_pedidos=row[1],
            status=row[2].value if row[2] else "sem status"
        )
        for row in proximas_entregas_query
    ]

    # Ingredientes necessários para próxima entrega (sábado)
    # Se hoje é segunda a sexta, próximo sábado é dentro de (5 - dia da semana) dias
    # Se hoje é sábado, próximo sábado é em 7 dias
    dias_para_sabado = (5 - hoje.weekday()) % 7
    if dias_para_sabado == 0:
        dias_para_sabado = 7

    proxima_entrega = hoje + timedelta(days=dias_para_sabado)

    # Calcular ingredientes necessários
    ingredientes_necessarios = None

    pedidos_proxima = db.query(models.Pedido).filter(
        models.Pedido.data_entrega >= proxima_entrega.replace(hour=0, minute=0, second=0, microsecond=0),
        models.Pedido.data_entrega < (proxima_entrega + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
        models.Pedido.status != models.StatusPedido.CANCELADO
    ).all()

    if pedidos_proxima:
        # Acumular ingredientes
        ingredientes_totais = {}

        for pedido in pedidos_proxima:
            for item in pedido.items:
                receita = db.query(models.Receita).filter(models.Receita.produto_id == item.produto_id).first()

                if not receita or not receita.quantidade_base:
                    continue

                for receita_ing in receita.ingredientes:
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

        ingredientes_necessarios = schemas.IngredientesNecessariosRead(
            data_entrega=proxima_entrega,
            ingredientes=[
                {
                    "id": ing_id,
                    "nome": ing_data["nome"],
                    "quantidade": round(ing_data["quantidade"], 2),
                    "unidade": ing_data["unidade"]
                }
                for ing_id, ing_data in ingredientes_totais.items()
            ],
            alertas=alertas
        )

    return schemas.DashboardHomeRead(
        proximasEntregas=proximas_entregas,
        ingredientesNecessarios=ingredientes_necessarios
    )
