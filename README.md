# Tuia Cucina

Sistema interno para organizar pedidos, produtos, receitas, ingredientes e estoque da padaria.

## Estrutura

- `backend/`: API FastAPI, autenticação, regras de negócio e acesso ao banco.
- `frontend/`: aplicação estática HTML, CSS e JavaScript, sem Angular ou dependências de runtime.
- `deployment/`: build estático para Cloudflare Pages e instruções de publicação.

## Desenvolvimento local

### API

No Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Use Python 3.13, a mesma versão definida no Dockerfile. O `.env.example` usa SQLite local. A aplicação cria as tabelas e carrega dados de demonstração quando o banco ainda não tem produtos. As contas fixas de demonstração são usadas somente em desenvolvimento; em produção, configure o administrador inicial pelas variáveis Railway descritas em [deployment/README.md](deployment/README.md). Consulte [seed.py](backend/app/seed.py).

### Interface

Em outro terminal, na raiz do repositório:

```powershell
python -m http.server 4173 --directory frontend
```

Abra `http://localhost:4173`. A configuração local em `frontend/config.js` aponta para `http://localhost:8000/api`.

## Deploy

O passo a passo para criar os serviços do zero e configurar variáveis está em [deployment/README.md](deployment/README.md). Os exemplos copiáveis ficam em [railway-api.variables.example.json](deployment/railway-api.variables.example.json) e [cloudflare-pages.variables.example.json](deployment/cloudflare-pages.variables.example.json).

## Funcionalidades

- Dashboard com próximas entregas, ingredientes previstos e alertas de estoque.
- Pedidos: criação, filtros, status e cancelamento.
- Produtos e receitas: cadastro, edição e exclusão.
- Ingredientes e estoque: cadastro, alertas, movimentos e histórico.
- Acesso por papéis: `admin`, `gerente` e `padeiro`; a autorização efetiva continua sendo validada pela API.

## API

Com a API em execução, a documentação interativa fica em `/docs`.
