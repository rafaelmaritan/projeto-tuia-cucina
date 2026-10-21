import {
  getCurrentUser,
  hasAnyRole,
  initializeAuth,
  login,
  logout,
  setCurrentUser,
} from './auth.js';
import { errorMessage, escapeHtml, feedbackMarkup } from './common.js';
import * as DashboardPage from './pages/dashboard.js';
import * as OrdersPage from './pages/orders.js';
import * as ProductsPage from './pages/products.js';
import * as RecipesPage from './pages/recipes.js';
import * as IngredientsPage from './pages/ingredients.js';
import * as StockPage from './pages/stock.js';

const root = document.querySelector('#app');
let loginNotice = '';

const pages = {
  dashboard: {
    title: 'Visão geral',
    roles: ['admin', 'gerente', 'padeiro'],
    render: DashboardPage.render,
  },
  pedidos: {
    title: 'Pedidos',
    roles: ['admin', 'gerente'],
    render: OrdersPage.renderList,
  },
  'pedido-novo': {
    title: 'Novo pedido',
    roles: ['admin', 'gerente'],
    render: OrdersPage.renderCreate,
  },
  produtos: {
    title: 'Produtos',
    roles: ['admin', 'gerente'],
    render: ProductsPage.render,
  },
  receitas: {
    title: 'Receitas',
    roles: ['admin', 'gerente', 'padeiro'],
    render: RecipesPage.render,
  },
  ingredientes: {
    title: 'Ingredientes',
    roles: ['admin', 'gerente'],
    render: IngredientsPage.render,
  },
  estoque: {
    title: 'Estoque',
    roles: ['admin', 'gerente'],
    render: StockPage.render,
  },
};

const navigation = [
  { path: 'dashboard', label: 'Visão geral', roles: ['admin', 'gerente', 'padeiro'] },
  { path: 'pedidos', label: 'Pedidos', roles: ['admin', 'gerente'] },
  { path: 'pedido-novo', label: 'Novo pedido', roles: ['admin', 'gerente'] },
  { path: 'produtos', label: 'Produtos', roles: ['admin', 'gerente'] },
  { path: 'receitas', label: 'Receitas', roles: ['admin', 'gerente', 'padeiro'] },
  { path: 'ingredientes', label: 'Ingredientes', roles: ['admin', 'gerente'] },
  { path: 'estoque', label: 'Estoque', roles: ['admin', 'gerente'] },
];

function currentPath() {
  return location.hash.replace(/^#\/?/, '').split('/')[0] || 'dashboard';
}

function renderLogin() {
  root.innerHTML = `
    <main class="login-layout">
      <section class="login-card" aria-labelledby="login-title">
        <a class="brand brand--login" href="#/login" aria-label="Tuia Cucina">
          <img class="login-brand-image" src="/assets/tuia.jpg" alt="Tuia Cucina">
        </a>
        <p class="eyebrow">MICROPADARIA ARTESANAL · FRANCA, SP</p>
        <h1 id="login-title">Buongiorno!</h1>
        <p class="muted">Entre para acompanhar nossa fornada e receber cada encomenda com carinho.</p>
        <div id="login-feedback">${feedbackMarkup(loginNotice, 'info')}</div>
        <form id="login-form" class="form-stack">
          <label for="login-email">E-mail</label>
          <input id="login-email" name="email" type="email" autocomplete="username" required>
          <label for="login-password">Senha</label>
          <input id="login-password" name="senha" type="password" autocomplete="current-password" required>
          <button class="button button--primary button--wide" type="submit">Entrar</button>
        </form>
        <p class="login-footnote">Acesso restrito à equipe Tuia Cucina.</p>
      </section>
      <aside class="login-aside" aria-hidden="true">
        <div class="login-aside-content">
          <img class="login-aside-logo" src="/assets/tuia.jpg" alt="">
          <p>Água, farinha<br>e tempo.</p>
          <span>Fermentação natural, nossa paixão.</span>
        </div>
      </aside>
    </main>
  `;

  const form = root.querySelector('#login-form');
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    button.textContent = 'Entrando…';
    loginNotice = '';

    try {
      const formData = new FormData(form);
      await login(String(formData.get('email')).trim(), String(formData.get('senha')));
      loginNotice = '';
      navigate('dashboard');
    } catch (error) {
      loginNotice = errorMessage(error);
      root.querySelector('#login-feedback').innerHTML = feedbackMarkup(loginNotice);
    } finally {
      button.disabled = false;
      button.textContent = 'Entrar';
    }
  });
}

function renderShell(page, pageKey) {
  const user = getCurrentUser();
  const links = navigation
    .filter((item) => item.roles.includes(user.papel))
    .map((item) => `
      <a class="nav-link ${item.path === pageKey ? 'is-active' : ''}" href="#/${item.path}">
        <span class="nav-dot" aria-hidden="true"></span>${item.label}
      </a>
    `)
    .join('');

  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" id="sidebar">
        <a class="brand" href="#/dashboard" aria-label="Tuia Cucina, visão geral">
          <span class="brand-emblem" aria-hidden="true"><img src="/assets/tuia.jpg" alt=""></span>
          <span><strong>Tuia</strong><small>Cucina</small></span>
        </a>
        <p class="sidebar-caption">ROTINA DA MICROPADARIA</p>
        <nav class="nav-menu" aria-label="Navegação principal">${links}</nav>
        <div class="sidebar-bottom">
          <span class="sidebar-note">Água, farinha<br>e tempo.</span>
        </div>
      </aside>
      <div class="workspace">
        <header class="topbar">
          <button class="menu-toggle" id="menu-toggle" type="button" aria-label="Abrir menu" aria-expanded="false">☰</button>
          <div class="topbar-title">
            <span class="eyebrow">TUIA CUCINA</span>
            <h1>${escapeHtml(page.title)}</h1>
          </div>
          <div class="user-menu">
            <span class="user-avatar">${escapeHtml((user.nome || 'T').slice(0, 1).toUpperCase())}</span>
            <span class="user-copy"><strong>${escapeHtml(user.nome)}</strong><small>${escapeHtml(user.papel)}</small></span>
            <button class="button button--quiet" id="logout-button" type="button">Sair</button>
          </div>
        </header>
        <main class="page-content" id="page-content" tabindex="-1"></main>
      </div>
    </div>
  `;

  root.querySelector('#menu-toggle').addEventListener('click', (event) => {
    const sidebar = root.querySelector('#sidebar');
    const isOpen = sidebar.classList.toggle('is-open');
    event.currentTarget.setAttribute('aria-expanded', String(isOpen));
  });
  root.querySelectorAll('.nav-link').forEach((link) => {
    link.addEventListener('click', () => {
      root.querySelector('#sidebar').classList.remove('is-open');
      root.querySelector('#menu-toggle').setAttribute('aria-expanded', 'false');
    });
  });
  root.querySelector('#logout-button').addEventListener('click', async () => {
    const button = root.querySelector('#logout-button');
    button.disabled = true;
    try {
      await logout();
    } catch {
      loginNotice = 'A sessão local foi encerrada, mas o servidor não confirmou o logout.';
    }
    navigate('login');
  });

  return root.querySelector('#page-content');
}

function navigate(path) {
  const nextHash = `#/${path}`;
  if (location.hash === nextHash) {
    void render();
  } else {
    location.hash = nextHash;
  }
}

function renderFatalError(error) {
  root.innerHTML = `
    <main class="fatal-screen">
      <section class="panel">
        <p class="eyebrow">CONEXÃO</p>
        <h1>Não foi possível iniciar</h1>
        ${feedbackMarkup(errorMessage(error))}
        <button class="button button--secondary" id="retry-connection" type="button">Tentar novamente</button>
      </section>
    </main>
  `;
  root.querySelector('#retry-connection').addEventListener('click', () => {
    void start();
  });
}

async function render() {
  if (!root) return;
  const user = getCurrentUser();
  const pageKey = currentPath();

  if (!user) {
    if (pageKey !== 'login') {
      navigate('login');
      return;
    }
    renderLogin();
    return;
  }

  if (pageKey === 'login') {
    navigate('dashboard');
    return;
  }

  const page = pages[pageKey];
  if (!page) {
    navigate('dashboard');
    return;
  }

  if (!page.roles.includes(user.papel)) {
    const content = renderShell({ title: 'Acesso restrito' }, pageKey);
    content.innerHTML = `
      <section class="panel">
        <p class="eyebrow">PERMISSÃO</p>
        <h2>Você não tem acesso a esta área</h2>
        <p class="muted">Seu perfil não permite abrir esta página.</p>
      </section>
    `;
    return;
  }

  const content = renderShell(page, pageKey);
  content.innerHTML = '<div class="loading-state">Carregando…</div>';
  try {
    await page.render(content);
  } catch (error) {
    content.innerHTML = `
      <section class="panel">
        <h2>Não foi possível carregar esta página</h2>
        ${feedbackMarkup(errorMessage(error))}
        <button class="button button--secondary" id="retry-page" type="button">Tentar novamente</button>
      </section>
    `;
    content.querySelector('#retry-page').addEventListener('click', () => {
      void render();
    });
  }
}

window.addEventListener('hashchange', () => {
  void render();
});

window.addEventListener('tuia:session-expired', () => {
  const hadActiveSession = getCurrentUser() !== null;
  setCurrentUser(null);
  loginNotice = hadActiveSession ? 'Sua sessão expirou. Entre novamente.' : '';
  if (currentPath() === 'login') {
    renderLogin();
  } else {
    navigate('login');
  }
});

async function start() {
  root.innerHTML = '<main class="boot-screen"><span class="brand-emblem" aria-hidden="true"><img src="/assets/tuia.jpg" alt=""></span><p>Conectando à Tuia Cucina…</p></main>';
  try {
    const user = await initializeAuth();
    if (!location.hash) {
      location.hash = user ? '#/dashboard' : '#/login';
    } else {
      await render();
    }
  } catch (error) {
    renderFatalError(error);
  }
}

void start();
