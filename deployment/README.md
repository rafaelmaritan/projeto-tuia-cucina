# Criar e publicar a Tuia Cucina do zero

O código fica em um único repositório Git; a publicação continua sendo feita em dois serviços: Railway para API/PostgreSQL e Cloudflare Pages para a interface estática. Este guia parte de um projeto novo nas duas plataformas.

## 0. Publicar o novo repositório Git

1. Crie no GitHub um repositório vazio chamado, por exemplo, `projeto-tuia-cucina`. Não marque as opções para adicionar README, `.gitignore` ou licença: o repositório local já contém esses arquivos.
2. Na raiz local `projeto-tuia-cucina`, confira o destino remoto:

   ```powershell
   git status --short --branch
   git remote -v
   ```

   O repositório local foi inicializado sem commits e seu tracking atual pode apontar para um `origin/main` indisponível.
3. Configure o remoto para o novo repositório. Se já existir `origin`:

   ```powershell
   git remote set-url origin https://github.com/SEU_USUARIO/projeto-tuia-cucina.git
   ```

   Se ainda não existir:

   ```powershell
   git remote add origin https://github.com/SEU_USUARIO/projeto-tuia-cucina.git
   ```

4. Crie e envie o primeiro commit:

   ```powershell
   git branch -M main
   git add .
   git commit -m "chore: bootstrap Tuia Cucina monorepo"
   git push -u origin main
   ```

   O `.gitignore` exclui arquivos `.env`, bancos locais, ambientes virtuais e builds. Não force a inclusão desses arquivos. Os repositórios antigos em `atual/` continuam como backup e não precisam ser conectados às plataformas.

## 1. Criar o PostgreSQL e a API no Railway

1. No Railway, crie um projeto novo, por exemplo `tuia-cucina`.
2. Adicione um serviço **PostgreSQL**. Para usar o exemplo fornecido sem alterações, mantenha o nome do serviço `Postgres`; se escolher outro nome, ajuste a referência `${{Postgres.DATABASE_URL}}`.
3. Adicione um serviço a partir do repositório GitHub `projeto-tuia-cucina` e selecione a branch `main`.
4. Nas configurações do serviço da API, defina o **Root Directory** como `/backend`. O Railway encontrará `railway.toml` e o Dockerfile nesse diretório. O arquivo configura o health check `/health`; o Dockerfile usa a porta `PORT` do Railway.
5. Antes de publicar, gere dois valores aleatórios locais:

   ```powershell
   python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(48)); print('INITIAL_ADMIN_PASSWORD=' + secrets.token_urlsafe(24))"
   ```

   Abra **Variables → Raw Editor** e cole o conteúdo de [railway-api.variables.example.json](railway-api.variables.example.json). Substitua `SECRET_KEY`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME` e `INITIAL_ADMIN_PASSWORD` por valores reais. Cole os segredos somente no Railway; não os grave no Git nem no JSON de exemplo. Mantenha `CORS_ORIGINS` vazio nesta primeira etapa. A referência `${{Postgres.DATABASE_URL}}` conecta a API ao banco Railway e o backend converte a URL para o driver `psycopg` 3.
6. Faça o primeiro deploy da API. No serviço, gere um domínio público e guarde a origem HTTPS, por exemplo `https://nome-do-servico.up.railway.app`. Não acrescente `/api`.
7. Verifique `https://nome-do-servico.up.railway.app/health`; o resultado esperado é HTTP 200. A API também disponibiliza `/docs`.

O primeiro início em um banco vazio cria as tabelas e carrega o catálogo de demonstração. Em `ENVIRONMENT=production`, a API cria somente o administrador definido por `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME` e `INITIAL_ADMIN_PASSWORD`; se esses valores forem inválidos ou estiverem ausentes, o serviço falha ao iniciar em vez de criar senhas conhecidas. Depois de confirmar o primeiro login, remova `INITIAL_ADMIN_PASSWORD` das variáveis Railway. As contas fixas de demonstração são usadas somente em desenvolvimento local.

## 2. Criar o frontend no Cloudflare Pages

1. No Cloudflare, crie um projeto em **Workers & Pages → Create → Pages → Connect to Git** e conecte o mesmo repositório GitHub.
2. Selecione a branch `main` e configure o build:

   | Configuração | Valor |
   | --- | --- |
   | Root directory | `/` |
   | Build command | `node deployment/build-frontend.mjs` |
   | Build output directory | `deployment/dist` |

   Não é necessário `npm install`: o build usa apenas Node.js e a biblioteca padrão.
3. Em **Settings → Environment variables**, adicione as variáveis do exemplo [cloudflare-pages.variables.example.json](cloudflare-pages.variables.example.json):

   - `NODE_VERSION`: `20`
   - `PUBLIC_API_BASE_URL`: a origem HTTPS obtida no Railway, sem `/api`, credenciais, barra final ou outro caminho. Exemplo: `https://nome-do-servico.up.railway.app`.

   `PUBLIC_API_BASE_URL` é pública e entra no JavaScript publicado; não coloque segredos nessa variável. Configure-a para o ambiente **Production**. Para usar Preview deployments, configure também o ambiente **Preview** e inclua as origens de preview na lista CORS do Railway.
4. Salve e faça o deploy. Anote a origem gerada pelo Pages, por exemplo `https://nome-do-projeto.pages.dev`.

O build valida a URL da API e falha se ela estiver ausente ou não for uma origem HTTPS. Ele cria a configuração pública do frontend sem incluir o `config.js` local de desenvolvimento.

## 3. Liberar o domínio do frontend no Railway

1. Volte ao serviço da API no Railway.
2. Em **Variables**, defina `CORS_ORIGINS` com a origem exata do Pages, sem barra final:

   ```text
   https://nome-do-projeto.pages.dev
   ```

   Se houver mais de uma origem autorizada, separe-as por vírgulas. Não use `*`: a API usa cookies com credenciais.
3. Salve e aguarde o redeploy da API.
4. Se adicionar domínio próprio ao Pages, atualize `CORS_ORIGINS` com essa origem exata também.

## 4. Validar a instalação

1. Abra o domínio Pages e teste o login com uma conta de demonstração.
2. Teste dashboard, pedido, receitas, produtos, ingredientes e movimentos de estoque.
3. Recarregue uma página protegida e confirme que a sessão continua válida; teste também logout e acesso por papéis diferentes.
4. No painel de rede do navegador, confirme que as chamadas `/api/*` chegam ao domínio Railway sem erro CORS.
5. Confirme que `/health` continua respondendo HTTP 200 e que a variável `DATABASE_URL` aponta para o PostgreSQL do projeto.

## Cookies e domínios

Em produção, a API define cookies `HttpOnly`, `Secure` e `SameSite=None`, necessários para chamadas com credenciais entre Cloudflare Pages e Railway. Os domínios padrão `*.pages.dev` e `*.up.railway.app` são sites diferentes e políticas de bloqueio de cookies de terceiros podem afetar o login em alguns navegadores. Antes de compartilhar o sistema, valide a sessão nos navegadores usados pela equipe. Para maior confiabilidade, use domínios próprios sob o mesmo domínio registrável, por exemplo `app.seudominio.com` e `api.seudominio.com`, e mantenha CORS restrito à origem da interface.

## Variáveis e segredos

- **Railway:** `DATABASE_URL`, `SECRET_KEY`, `ENVIRONMENT`, `DEBUG`, `SQLALCHEMY_ECHO`, `INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_NAME`, `INITIAL_ADMIN_PASSWORD` e `CORS_ORIGINS`.
- **Cloudflare Pages:** `PUBLIC_API_BASE_URL` e `NODE_VERSION`.
- Nunca configure `SECRET_KEY` ou credenciais do banco no Cloudflare Pages: todo valor usado no build do frontend pode ficar público.
