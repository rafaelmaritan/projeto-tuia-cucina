from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import enum

Base = declarative_base()


# ==================== ENUMS ====================
class StatusPedido(str, enum.Enum):
    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    PRODUCAO = "produção"
    PRONTO = "pronto"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class TipoEntrega(str, enum.Enum):
    RETIRADA = "retirada"
    ENTREGA = "entrega"


class TipoMovimento(str, enum.Enum):
    ENTRADA = "entrada"  # Compra de ingrediente
    SAIDA = "saída"      # Consumo em produção
    AJUSTE = "ajuste"    # Ajuste manual


class Papel(str, enum.Enum):
    ADMIN = "admin"
    GERENTE = "gerente"
    PADEIRO = "padeiro"


# ==================== PRODUTOS ====================
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    descricao = Column(Text)
    preco_varejo = Column(Float, nullable=False)
    preco_custo = Column(Float)

    # Relacionamentos
    receita = relationship("Receita", back_populates="produto", uselist=False, cascade="all, delete-orphan")
    pedido_items = relationship("PedidoItem", back_populates="produto")

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== RECEITAS ====================
class Receita(Base):
    __tablename__ = "receitas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade_base = Column(Integer)  # 20 focacias (base para cálculo)

    tempo_fermentacao_horas = Column(Integer)
    tempo_assamento_minutos = Column(Integer)
    instrucoes = Column(Text)

    # Relacionamentos
    produto = relationship("Produto", back_populates="receita")
    ingredientes = relationship("ReceitaIngrediente", back_populates="receita", cascade="all, delete-orphan")

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== INGREDIENTES ====================
class Ingrediente(Base):
    __tablename__ = "ingredientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False, unique=True)
    unidade = Column(String(20))  # "kg", "L", "g"
    preco_unitario = Column(Float)

    # Relacionamentos
    receita_ingredientes = relationship("ReceitaIngrediente", back_populates="ingrediente")
    estoque = relationship("Estoque", back_populates="ingrediente", uselist=False, cascade="all, delete-orphan")

    criado_em = Column(DateTime, default=datetime.utcnow)


# ==================== RECEITA-INGREDIENTE (Many-to-Many) ====================
class ReceitaIngrediente(Base):
    __tablename__ = "receita_ingredientes"

    id = Column(Integer, primary_key=True, index=True)
    receita_id = Column(Integer, ForeignKey("receitas.id"), nullable=False)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), nullable=False)
    quantidade = Column(Float, nullable=False)

    # Relacionamentos
    receita = relationship("Receita", back_populates="ingredientes")
    ingrediente = relationship("Ingrediente", back_populates="receita_ingredientes")


# ==================== ESTOQUE ====================
class Estoque(Base):
    __tablename__ = "estoque"

    id = Column(Integer, primary_key=True, index=True)
    ingrediente_id = Column(Integer, ForeignKey("ingredientes.id"), nullable=False)
    quantidade = Column(Float, nullable=False, default=0)
    quantidade_minima = Column(Float, default=0)

    # Relacionamentos
    ingrediente = relationship("Ingrediente", back_populates="estoque")
    movimentos = relationship("EstoqueMovimento", back_populates="estoque", cascade="all, delete-orphan")

    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== ESTOQUE MOVIMENTO ====================
class EstoqueMovimento(Base):
    __tablename__ = "estoque_movimentos"

    id = Column(Integer, primary_key=True, index=True)
    estoque_id = Column(Integer, ForeignKey("estoque.id"), nullable=False)
    tipo = Column(Enum(TipoMovimento), nullable=False)
    quantidade = Column(Float, nullable=False)
    observacao = Column(Text)

    # Relacionamentos
    estoque = relationship("Estoque", back_populates="movimentos")

    criado_em = Column(DateTime, default=datetime.utcnow, index=True)


# ==================== PEDIDOS ====================
class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    numero_pedido = Column(String(20), unique=True, index=True)

    # Usuário (owner check)
    usuario_criador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)

    # Cliente
    cliente_nome = Column(String(255), nullable=False)
    cliente_email = Column(String(255))
    cliente_telefone = Column(String(20))

    # Entrega
    data_entrega = Column(DateTime, nullable=False, index=True)
    tipo_entrega = Column(Enum(TipoEntrega), default=TipoEntrega.RETIRADA)
    endereco_entrega = Column(Text)

    # Pedido
    status = Column(Enum(StatusPedido), default=StatusPedido.PENDENTE, index=True)
    valor_total = Column(Float)
    observacoes = Column(Text)

    # Pagamento
    metodo_pagamento = Column(String(50))
    comprovante_pagamento = Column(String(255))
    data_pagamento = Column(DateTime)

    # Relacionamentos
    items = relationship("PedidoItem", back_populates="pedido", cascade="all, delete-orphan")
    usuario = relationship("Usuario")

    criado_em = Column(DateTime, default=datetime.utcnow, index=True)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== PEDIDO-ITEM ====================
class PedidoItem(Base):
    __tablename__ = "pedido_items"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)

    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)
    subtotal = Column(Float)

    # Relacionamentos
    pedido = relationship("Pedido", back_populates="items")
    produto = relationship("Produto", back_populates="pedido_items")


# ==================== USUÁRIOS ====================
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    nome = Column(String(255), nullable=False)
    senha_hash = Column(String(255), nullable=False)
    papel = Column(Enum(Papel), default=Papel.GERENTE, nullable=False)
    ativo = Column(Integer, default=1)

    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
