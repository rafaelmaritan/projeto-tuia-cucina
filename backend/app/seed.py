"""
Script para criar dados iniciais no banco de dados
Roda durante o start do sistema
"""
from app.database import SessionLocal
from app import models
from app.config import settings
from app.security.password import hash_senha
from datetime import datetime


def _seed_initial_users(db):
    if db.query(models.Usuario).count() > 0:
        return

    if settings.ENVIRONMENT.lower() == "production":
        email = settings.INITIAL_ADMIN_EMAIL.strip().lower()
        nome = settings.INITIAL_ADMIN_NAME.strip()
        senha = settings.INITIAL_ADMIN_PASSWORD
        if not email or "@" not in email:
            raise ValueError("INITIAL_ADMIN_EMAIL must be a valid email in production")
        if not nome:
            raise ValueError("INITIAL_ADMIN_NAME is required in production")
        if len(senha.encode("utf-8")) < 16 or len(senha.encode("utf-8")) > 72:
            raise ValueError("INITIAL_ADMIN_PASSWORD must contain between 16 and 72 UTF-8 bytes")
        usuarios_data = [{
            "email": email,
            "nome": nome,
            "senha": senha,
            "papel": models.Papel.ADMIN,
        }]
    else:
        usuarios_data = [
            {
                "email": "admin@tuia.com",
                "nome": "Administrador",
                "senha": "admin123",
                "papel": models.Papel.ADMIN
            },
            {
                "email": "gerente@tuia.com",
                "nome": "Gerente de Operações",
                "senha": "gerente123",
                "papel": models.Papel.GERENTE
            },
            {
                "email": "padeiro@tuia.com",
                "nome": "Padeiro",
                "senha": "padeiro123",
                "papel": models.Papel.PADEIRO
            }
        ]

    for user_data in usuarios_data:
        usuario = models.Usuario(
            email=user_data["email"],
            nome=user_data["nome"],
            senha_hash=hash_senha(user_data["senha"]),
            papel=user_data["papel"],
            ativo=1
        )
        db.add(usuario)
        print(f"  ✓ Usuário inicial: {user_data['email']} ({user_data['papel']})")


def seed_database():
    """Popula banco com dados iniciais"""
    db = SessionLocal()

    try:
        # Preservar o catálogo existente, mas permitir o bootstrap inicial do usuário.
        if db.query(models.Produto).count() > 0:
            print("Banco já contém dados. Skip seed.")
            _seed_initial_users(db)
            db.commit()
            return

        print("🌱 Iniciando seed do banco de dados...")

        # ==================== INGREDIENTES ====================
        ingredientes_data = [
            {"nome": "Farinha", "unidade": "kg", "preco_unitario": 5.0},
            {"nome": "Água", "unidade": "L", "preco_unitario": 0.5},
            {"nome": "Sal", "unidade": "kg", "preco_unitario": 8.0},
            {"nome": "Azeite", "unidade": "L", "preco_unitario": 35.0},
            {"nome": "Massa mãe", "unidade": "kg", "preco_unitario": 10.0},
            {"nome": "Mel", "unidade": "kg", "preco_unitario": 25.0},
            {"nome": "Canela", "unidade": "kg", "preco_unitario": 50.0},
            {"nome": "Açúcar", "unidade": "kg", "preco_unitario": 3.0},
            {"nome": "Manteiga", "unidade": "kg", "preco_unitario": 15.0},
            {"nome": "Ovos", "unidade": "dúzia", "preco_unitario": 12.0},
            {"nome": "Fermento biológico", "unidade": "kg", "preco_unitario": 20.0},
        ]

        ingredientes = {}
        for ing_data in ingredientes_data:
            ing = models.Ingrediente(**ing_data)
            db.add(ing)
            db.flush()
            ingredientes[ing_data["nome"]] = ing.id
            print(f"  ✓ Ingrediente: {ing_data['nome']}")

        # ==================== PRODUTOS ====================
        produtos_data = [
            {"nome": "Focaccia", "descricao": "Pão italiano focaccia", "preco_varejo": 15.0, "preco_custo": 4.0},
            {"nome": "Pão Multigrãos", "descricao": "Pão com múltiplos grãos", "preco_varejo": 12.0, "preco_custo": 3.5},
            {"nome": "Cinnamon Rolls", "descricao": "Pão doce com canela", "preco_varejo": 18.0, "preco_custo": 5.0},
            {"nome": "Baguete", "descricao": "Baguete francesa clássica", "preco_varejo": 10.0, "preco_custo": 2.5},
            {"nome": "Pão de Queijo", "descricao": "Pão de queijo mineiro", "preco_varejo": 14.0, "preco_custo": 4.0},
            {"nome": "Croissant", "descricao": "Croissant folhado", "preco_varejo": 16.0, "preco_custo": 5.0},
            {"nome": "Pão Integral", "descricao": "Pão integral 100%", "preco_varejo": 11.0, "preco_custo": 3.0},
            {"nome": "Broa de Milho", "descricao": "Broa tradicional de milho", "preco_varejo": 13.0, "preco_custo": 3.5},
            {"nome": "Pão Doce", "descricao": "Pão doce com mel", "preco_varejo": 15.0, "preco_custo": 4.0},
            {"nome": "Bisnaga", "descricao": "Bisnaga macia", "preco_varejo": 8.0, "preco_custo": 2.0},
            {"nome": "Pão de Alho", "descricao": "Pão com alho e ervas", "preco_varejo": 12.0, "preco_custo": 3.0},
        ]

        produtos = {}
        for prod_data in produtos_data:
            prod = models.Produto(**prod_data)
            db.add(prod)
            db.flush()
            produtos[prod_data["nome"]] = prod.id
            print(f"  ✓ Produto: {prod_data['nome']}")

        # ==================== RECEITAS ====================
        receitas_data = [
            {
                "nome": "Focaccia Italiana com Azeite",
                "produto_nome": "Focaccia",
                "quantidade_base": 20,
                "tempo_fermentacao_horas": 18,
                "tempo_assamento_minutos": 35,
                "instrucoes": "1. Misturar farinha + água + sal + massa mãe (5 min)\n2. Descansar 30 min\n3. Amassar + azeite (5 min)\n4. Moldar focacias\n5. Fermentar overnight (12-24h)\n6. Assar 220°C / 30-40 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 5},
                    {"nome": "Água", "quantidade": 3.5},
                    {"nome": "Sal", "quantidade": 0.1},
                    {"nome": "Azeite", "quantidade": 0.2},
                    {"nome": "Massa mãe", "quantidade": 0.5},
                ]
            },
            {
                "nome": "Pão Multigrãos Integral",
                "produto_nome": "Pão Multigrãos",
                "quantidade_base": 15,
                "tempo_fermentacao_horas": 12,
                "tempo_assamento_minutos": 40,
                "instrucoes": "1. Misturar farinha + água + sal + sementes\n2. Descansar 1h\n3. Moldar\n4. Fermentar 12h\n5. Assar 220°C / 40 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 4},
                    {"nome": "Água", "quantidade": 2.5},
                    {"nome": "Sal", "quantidade": 0.08},
                    {"nome": "Massa mãe", "quantidade": 0.4},
                ]
            },
            {
                "nome": "Cinnamon Rolls Doces",
                "produto_nome": "Cinnamon Rolls",
                "quantidade_base": 30,
                "tempo_fermentacao_horas": 2,
                "tempo_assamento_minutos": 25,
                "instrucoes": "1. Preparar massa doce\n2. Enrolar com canela e açúcar\n3. Cortar\n4. Fermentar 2h\n5. Assar 190°C / 25 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 2},
                    {"nome": "Água", "quantidade": 1},
                    {"nome": "Manteiga", "quantidade": 0.3},
                    {"nome": "Açúcar", "quantidade": 0.4},
                    {"nome": "Canela", "quantidade": 0.05},
                ]
            },
            {
                "nome": "Baguete Francesa Clássica",
                "produto_nome": "Baguete",
                "quantidade_base": 10,
                "tempo_fermentacao_horas": 16,
                "tempo_assamento_minutos": 30,
                "instrucoes": "1. Massa clássica francesa\n2. Fermentação longa\n3. Moldagem em baguete\n4. Assar 230°C / 30 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 3},
                    {"nome": "Água", "quantidade": 2},
                    {"nome": "Sal", "quantidade": 0.06},
                    {"nome": "Fermento biológico", "quantidade": 0.01},
                ]
            },
            {
                "nome": "Pão de Queijo Mineiro",
                "produto_nome": "Pão de Queijo",
                "quantidade_base": 20,
                "tempo_fermentacao_horas": 0,
                "tempo_assamento_minutos": 20,
                "instrucoes": "1. Polvilho azedo + queijo + ovos + manteiga\n2. Assar direto 200°C / 20 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 2},
                    {"nome": "Ovos", "quantidade": 0.5},
                    {"nome": "Manteiga", "quantidade": 0.2},
                ]
            },
            {
                "nome": "Croissant Folhado",
                "produto_nome": "Croissant",
                "quantidade_base": 12,
                "tempo_fermentacao_horas": 18,
                "tempo_assamento_minutos": 20,
                "instrucoes": "1. Massa folhada com manteiga\n2. Dobras múltiplas\n3. Fermentação 18h\n4. Assar 200°C / 20 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 2.5},
                    {"nome": "Manteiga", "quantidade": 1},
                    {"nome": "Água", "quantidade": 1},
                    {"nome": "Sal", "quantidade": 0.05},
                ]
            },
            {
                "nome": "Pão Integral 100%",
                "produto_nome": "Pão Integral",
                "quantidade_base": 12,
                "tempo_fermentacao_horas": 12,
                "tempo_assamento_minutos": 45,
                "instrucoes": "1. Farinha integral 100%\n2. Fermentação 12h\n3. Assar 210°C / 45 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 4},
                    {"nome": "Água", "quantidade": 2.5},
                    {"nome": "Sal", "quantidade": 0.08},
                    {"nome": "Mel", "quantidade": 0.1},
                ]
            },
            {
                "nome": "Broa de Milho Tradicional",
                "produto_nome": "Broa de Milho",
                "quantidade_base": 10,
                "tempo_fermentacao_horas": 8,
                "tempo_assamento_minutos": 50,
                "instrucoes": "1. Mistura farinha + fubá\n2. Fermentação 8h\n3. Assar 200°C / 50 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 2},
                    {"nome": "Água", "quantidade": 2},
                    {"nome": "Sal", "quantidade": 0.06},
                ]
            },
            {
                "nome": "Pão Doce com Mel",
                "produto_nome": "Pão Doce",
                "quantidade_base": 15,
                "tempo_fermentacao_horas": 4,
                "tempo_assamento_minutos": 30,
                "instrucoes": "1. Massa com mel e açúcar\n2. Fermentação 4h\n3. Assar 190°C / 30 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 3},
                    {"nome": "Mel", "quantidade": 0.5},
                    {"nome": "Açúcar", "quantidade": 0.3},
                    {"nome": "Água", "quantidade": 1.5},
                ]
            },
            {
                "nome": "Bisnaga Macia e Fofa",
                "produto_nome": "Bisnaga",
                "quantidade_base": 40,
                "tempo_fermentacao_horas": 2,
                "tempo_assamento_minutos": 20,
                "instrucoes": "1. Massa mole e doce\n2. Fermentação rápida 2h\n3. Assar 190°C / 20 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 2},
                    {"nome": "Água", "quantidade": 1.2},
                    {"nome": "Manteiga", "quantidade": 0.2},
                    {"nome": "Açúcar", "quantidade": 0.2},
                ]
            },
            {
                "nome": "Pão de Alho com Ervas",
                "produto_nome": "Pão de Alho",
                "quantidade_base": 12,
                "tempo_fermentacao_horas": 6,
                "tempo_assamento_minutos": 25,
                "instrucoes": "1. Base de pão branco\n2. Cobertura com alho e ervas\n3. Fermentação 6h\n4. Assar 200°C / 25 min",
                "ingredientes": [
                    {"nome": "Farinha", "quantidade": 3},
                    {"nome": "Água", "quantidade": 2},
                    {"nome": "Azeite", "quantidade": 0.15},
                    {"nome": "Sal", "quantidade": 0.06},
                ]
            }]

        for receita_data in receitas_data:
            receita = models.Receita(
                nome=receita_data["nome"],
                produto_id=produtos[receita_data["produto_nome"]],
                quantidade_base=receita_data["quantidade_base"],
                tempo_fermentacao_horas=receita_data["tempo_fermentacao_horas"],
                tempo_assamento_minutos=receita_data["tempo_assamento_minutos"],
                instrucoes=receita_data["instrucoes"]
            )
            db.add(receita)
            db.flush()

            # Adicionar ingredientes à receita
            for ing_data in receita_data["ingredientes"]:
                receita_ing = models.ReceitaIngrediente(
                    receita_id=receita.id,
                    ingrediente_id=ingredientes[ing_data["nome"]],
                    quantidade=ing_data["quantidade"]
                )
                db.add(receita_ing)

            print(f"  ✓ Receita: {receita_data['nome']}")

        # ==================== ESTOQUE ====================
        for ing_id in ingredientes.values():
            estoque = models.Estoque(
                ingrediente_id=ing_id,
                quantidade=100,  # Quantidade inicial grande
                quantidade_minima=10
            )
            db.add(estoque)

        print("  ✓ Estoques criados")

        # ==================== USUÁRIO INICIAL ====================
        _seed_initial_users(db)

        # Commitar tudo
        db.commit()
        print("\n✅ Seed concluído com sucesso!")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro durante seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
