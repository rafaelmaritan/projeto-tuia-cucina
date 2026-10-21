from pydantic import BaseModel, EmailStr, Field, field_validator, computed_field
from datetime import datetime
from typing import Optional, List
from app.models import StatusPedido, TipoEntrega


# ==================== PRODUTOS ====================
class ProdutoBase(BaseModel):
    nome: str
    descricao: Optional[str] = None
    preco_varejo: float
    preco_custo: Optional[float] = None


class ProdutoCreate(ProdutoBase):
    pass


class ProdutoRead(ProdutoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# ==================== INGREDIENTES ====================
class IngredienteBase(BaseModel):
    nome: str
    unidade: Optional[str] = None
    preco_unitario: Optional[float] = None


class IngredienteCreate(IngredienteBase):
    pass


class IngredienteRead(IngredienteBase):
    id: int
    criado_em: datetime

    class Config:
        from_attributes = True


# ==================== RECEITA INGREDIENTE ====================
class ReceitaIngredienteBase(BaseModel):
    ingrediente_id: int
    quantidade: float


class ReceitaIngredienteRead(ReceitaIngredienteBase):
    id: int
    ingrediente: IngredienteRead

    class Config:
        from_attributes = True


# ==================== RECEITAS ====================
class ReceitaBase(BaseModel):
    nome: str
    quantidade_base: Optional[int] = None
    tempo_fermentacao_horas: Optional[int] = None
    tempo_assamento_minutos: Optional[int] = None
    instrucoes: Optional[str] = None


class ReceitaCreate(ReceitaBase):
    produto_id: int
    ingredientes: Optional[List[ReceitaIngredienteBase]] = []


class ReceitaUpdate(BaseModel):
    nome: Optional[str] = None
    quantidade_base: Optional[int] = None
    ingredientes: Optional[List[ReceitaIngredienteBase]] = None
    tempo_fermentacao_horas: Optional[int] = None
    tempo_assamento_minutos: Optional[int] = None
    instrucoes: Optional[str] = None


class ReceitaRead(ReceitaBase):
    id: int
    nome: str
    produto_id: int
    ingredientes: List[ReceitaIngredienteRead] = []
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# ==================== ESTOQUE ====================
class EstoqueBase(BaseModel):
    quantidade: float
    quantidade_minima: float = 0


class EstoqueCreate(EstoqueBase):
    ingrediente_id: int


class EstoqueUpdate(BaseModel):
    quantidade: float


class EstoqueRead(EstoqueBase):
    id: int
    ingrediente_id: int
    atualizado_em: datetime

    class Config:
        from_attributes = True


class EstoqueMovimentoBase(BaseModel):
    tipo: str  # "entrada", "saída", "ajuste"
    quantidade: float = Field(gt=0)
    observacao: Optional[str] = None


class EstoqueMovimentoCreate(EstoqueMovimentoBase):
    estoque_id: int


class EstoqueMovimentoRead(EstoqueMovimentoBase):
    id: int
    estoque_id: int
    criado_em: datetime

    class Config:
        from_attributes = True


class EstoqueComMovimentos(EstoqueRead):
    movimentos: List[EstoqueMovimentoRead] = []


# ==================== PEDIDO ITEMS ====================
class PedidoItemBase(BaseModel):
    produto_id: int
    quantidade: int = Field(gt=0)


class PedidoItemCreate(PedidoItemBase):
    pass


class ProdutoSimples(BaseModel):
    """Modelo simplificado de Produto para incluir em PedidoItem"""
    id: int
    nome: str

    class Config:
        from_attributes = True


class PedidoItemRead(PedidoItemBase):
    id: int
    preco_unitario: float
    subtotal: float
    produto: Optional[ProdutoSimples] = None  # Incluir o objeto produto completo

    @computed_field  # type: ignore
    @property
    def produto_nome(self) -> str:
        """Extrai o nome do produto a partir da relação SQLAlchemy"""
        if self.produto:
            return self.produto.nome
        return ""

    class Config:
        from_attributes = True


# ==================== PEDIDOS ====================
class PedidoBase(BaseModel):
    cliente_nome: str
    cliente_email: EmailStr
    cliente_telefone: str
    data_entrega: datetime
    tipo_entrega: TipoEntrega = TipoEntrega.RETIRADA
    endereco_entrega: Optional[str] = None
    observacoes: Optional[str] = None


class PedidoCreate(PedidoBase):
    items: List[PedidoItemCreate]

    @field_validator("items")
    @classmethod
    def items_not_empty(cls, v):
        if not v:
            raise ValueError("Pedido deve ter pelo menos 1 item")
        return v


class PedidoUpdate(BaseModel):
    cliente_nome: Optional[str] = None
    cliente_email: Optional[EmailStr] = None
    cliente_telefone: Optional[str] = None
    observacoes: Optional[str] = None
    items: Optional[List[PedidoItemCreate]] = None


class PedidoStatusUpdate(BaseModel):
    status: StatusPedido


class PedidoRead(PedidoBase):
    id: int
    numero_pedido: str
    status: StatusPedido
    valor_total: float
    items: List[PedidoItemRead] = []
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


# ==================== DASHBOARD ====================
class ProximaEntregaRead(BaseModel):
    data: datetime
    total_pedidos: int
    status: str


class IngredientesAlertaRead(BaseModel):
    ingrediente_id: int
    ingrediente_nome: str
    necessario: float
    disponivel: float
    diferenca: float
    unidade: str


class IngredientesNecessariosRead(BaseModel):
    data_entrega: datetime
    ingredientes: List[dict]  # { id, nome, quantidade, unidade }
    alertas: List[IngredientesAlertaRead]


class DashboardHomeRead(BaseModel):
    proximasEntregas: List[ProximaEntregaRead]
    ingredientesNecessarios: Optional[IngredientesNecessariosRead]
