import { api } from '../api.js';
import {
  errorMessage,
  escapeHtml,
  feedbackMarkup,
  formatCurrency,
  formatDateTime,
  statusClass,
  statusLabel,
} from '../common.js';

const statusTransitions = {
  pendente: ['confirmado', 'cancelado'],
  confirmado: ['produção', 'cancelado'],
  produção: ['pronto'],
  pronto: ['entregue'],
  entregue: [],
  cancelado: [],
};

const allStatuses = [
  'pendente',
  'confirmado',
  'produção',
  'pronto',
  'entregue',
  'cancelado',
];

export async function renderList(container) {
  let filters = { status: '', data_entrega: '' };
  let feedback = '';
  let feedbackType = 'success';

  async function draw() {
    container.innerHTML = '<div class="loading-state">Carregando pedidos…</div>';
    const params = new URLSearchParams();
    if (filters.status) params.set('status', filters.status);
    if (filters.data_entrega) {
      params.set('data_entrega', `${filters.data_entrega}T00:00:00`);
    }
    const query = params.size ? `?${params.toString()}` : '';
    const orders = await api(`/pedidos${query}`);

    container.innerHTML = `
      <section class="page-heading">
        <div><h2>Pedidos da padaria</h2><p>Acompanhe prazos, itens e andamento de cada encomenda.</p></div>
        <a class="button button--primary" href="#/pedido-novo">Novo pedido</a>
      </section>
      ${feedbackMarkup(feedback, feedbackType)}
      <section class="panel">
        <form id="order-filters" class="filter-bar">
          <div class="field">
            <label for="filter-status">Status</label>
            <select id="filter-status" name="status">
              <option value="">Todos os status</option>
              ${allStatuses.map((status) => `<option value="${escapeHtml(status)}" ${filters.status === status ? 'selected' : ''}>${escapeHtml(statusLabel(status))}</option>`).join('')}
            </select>
          </div>
          <div class="field">
            <label for="filter-date">Data de entrega</label>
            <input id="filter-date" name="data_entrega" type="date" value="${escapeHtml(filters.data_entrega)}">
          </div>
          <button class="button button--secondary" type="submit">Aplicar filtros</button>
          <button class="button button--quiet" id="clear-filters" type="button">Limpar</button>
        </form>
        ${orders.length ? `
          <div class="data-table-wrap"><table class="data-table">
            <thead><tr><th>Pedido</th><th>Cliente</th><th>Entrega</th><th>Itens</th><th>Total</th><th>Status</th><th>Ações</th></tr></thead>
            <tbody>${orders.map((order) => {
              const transitions = statusTransitions[order.status] || [];
              const itemSummary = (order.items || []).map((item) =>
                `${item.quantidade} × ${escapeHtml(item.produto_nome || `Produto ${item.produto_id}`)}`,
              ).join('<br>');
              return `<tr>
                <td><strong>${escapeHtml(order.numero_pedido)}</strong></td>
                <td>${escapeHtml(order.cliente_nome)}<small class="table-secondary">${escapeHtml(order.cliente_telefone || '')}</small></td>
                <td>${formatDateTime(order.data_entrega)}<small class="table-secondary">${order.tipo_entrega === 'entrega' ? 'Entrega' : 'Retirada'}</small></td>
                <td>${itemSummary || '—'}</td>
                <td>${formatCurrency(order.valor_total)}</td>
                <td><span class="badge badge--${statusClass(order.status)}">${escapeHtml(statusLabel(order.status))}</span></td>
                <td><div class="table-actions">
                  ${transitions.length ? `<select class="compact-select" aria-label="Alterar status do pedido ${escapeHtml(order.numero_pedido)}" data-order-status="${order.id}">
                    <option value="">Alterar status</option>
                    ${transitions.map((status) => `<option value="${escapeHtml(status)}">${escapeHtml(statusLabel(status))}</option>`).join('')}
                  </select>` : ''}
                  ${!['entregue', 'cancelado'].includes(order.status) ? `<button class="button button--danger button--small" type="button" data-cancel-order="${order.id}">Cancelar</button>` : ''}
                </div></td>
              </tr>
              <tr class="detail-row"><td colspan="7"><div class="detail-content">
                <strong>Contato:</strong> ${escapeHtml(order.cliente_email || 'sem e-mail')}
                ${order.endereco_entrega ? ` · <strong>Endereço:</strong> ${escapeHtml(order.endereco_entrega)}` : ''}
                ${order.observacoes ? `<br><strong>Observações:</strong> ${escapeHtml(order.observacoes)}` : ''}
              </div></td></tr>`;
            }).join('')}</tbody>
          </table></div>`
          : '<div class="empty-state"><p>Nenhum pedido encontrado com esses filtros.</p></div>'}
      </section>
    `;

    container.querySelector('#order-filters').addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      filters = {
        status: String(form.get('status') || ''),
        data_entrega: String(form.get('data_entrega') || ''),
      };
      feedback = '';
      await draw();
    });
    container.querySelector('#clear-filters').addEventListener('click', async () => {
      filters = { status: '', data_entrega: '' };
      feedback = '';
      await draw();
    });
    container.querySelectorAll('[data-order-status]').forEach((select) => {
      select.addEventListener('change', async (event) => {
        const orderId = event.currentTarget.dataset.orderStatus;
        const newStatus = event.currentTarget.value;
        if (!newStatus) return;
        try {
          await api(`/pedidos/${orderId}/status`, {
            method: 'PATCH',
            body: { status: newStatus },
          });
          feedback = `Status atualizado para ${statusLabel(newStatus)}.`;
          feedbackType = 'success';
        } catch (error) {
          feedback = errorMessage(error);
          feedbackType = 'error';
        }
        await draw();
      });
    });
    container.querySelectorAll('[data-cancel-order]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        const orderId = event.currentTarget.dataset.cancelOrder;
        if (!window.confirm('Tem certeza que deseja cancelar este pedido?')) return;
        try {
          await api(`/pedidos/${orderId}`, { method: 'DELETE' });
          feedback = 'Pedido cancelado.';
          feedbackType = 'success';
        } catch (error) {
          feedback = errorMessage(error);
          feedbackType = 'error';
        }
        await draw();
      });
    });
  }

  await draw();
}

export async function renderCreate(container) {
  const products = await api('/produtos');
  let selectedItems = [];
  let feedback = '';
  let feedbackType = 'error';

  container.innerHTML = `
    <section class="page-heading">
      <div><h2>Registrar encomenda</h2><p>Informe os dados do cliente, a entrega e os produtos.</p></div>
      <a class="button button--secondary" href="#/pedidos">Voltar aos pedidos</a>
    </section>
    <section class="panel">
      <div id="order-create-feedback">${feedbackMarkup(feedback, feedbackType)}</div>
      <form id="create-order-form">
        <div class="form-grid">
          <div class="field"><label for="customer-name">Nome do cliente</label><input id="customer-name" name="cliente_nome" required minlength="3" autocomplete="name"></div>
          <div class="field"><label for="customer-email">E-mail</label><input id="customer-email" name="cliente_email" type="email" required autocomplete="email"></div>
          <div class="field"><label for="customer-phone">Telefone</label><input id="customer-phone" name="cliente_telefone" type="tel" required maxlength="20" autocomplete="tel"></div>
          <div class="field"><label for="delivery-date">Data e hora de entrega</label><input id="delivery-date" name="data_entrega" type="datetime-local" required></div>
          <div class="field"><label for="delivery-type">Tipo</label>
            <select id="delivery-type" name="tipo_entrega" required>
              <option value="retirada">Retirada</option><option value="entrega">Entrega</option>
            </select>
          </div>
          <div class="field" id="address-field" hidden><label for="delivery-address">Endereço de entrega</label><input id="delivery-address" name="endereco_entrega" autocomplete="street-address"></div>
          <div class="field field--wide"><label for="order-notes">Observações</label><textarea id="order-notes" name="observacoes" rows="3"></textarea></div>
        </div>

        <div class="panel panel--nested">
          <div class="panel-heading"><div><h3>Itens do pedido</h3><p>O preço registrado será o preço atual do produto.</p></div></div>
          ${products.length ? `
            <div class="inline-form">
              <div class="field"><label for="item-product">Produto</label>
                <select id="item-product"><option value="">Selecione um produto</option>
                  ${products.map((product) => `<option value="${product.id}">${escapeHtml(product.nome)} — ${formatCurrency(product.preco_varejo)}</option>`).join('')}
                </select>
              </div>
              <div class="field"><label for="item-quantity">Quantidade</label><input id="item-quantity" type="number" min="1" step="1" value="1"></div>
              <button class="button button--secondary" id="add-order-item" type="button">Adicionar item</button>
            </div>`
            : '<div class="empty-state"><p>Cadastre um produto antes de criar um pedido.</p></div>'}
          <div id="selected-order-items"></div>
        </div>
        <div class="form-actions">
          <button class="button button--primary" type="submit" ${products.length ? '' : 'disabled'}>Criar pedido</button>
          <a class="button button--quiet" href="#/pedidos">Cancelar</a>
        </div>
      </form>
    </section>
  `;

  const itemsContainer = container.querySelector('#selected-order-items');
  const renderItems = () => {
    if (!selectedItems.length) {
      itemsContainer.innerHTML = '<div class="empty-state"><p>Adicione pelo menos um produto ao pedido.</p></div>';
      return;
    }
    const total = selectedItems.reduce((sum, item) => sum + item.preco_varejo * item.quantidade, 0);
    itemsContainer.innerHTML = `
      <div class="item-list">${selectedItems.map((item, index) => `
        <div class="item-line">
          <span>${escapeHtml(item.nome)} · ${item.quantidade} × ${formatCurrency(item.preco_varejo)}</span>
          <span>${formatCurrency(item.preco_varejo * item.quantidade)}
            <button class="link-button" type="button" data-remove-item="${index}" aria-label="Remover ${escapeHtml(item.nome)}">Remover</button>
          </span>
        </div>`).join('')}</div>
      <div class="total-line"><span>Total previsto</span><span>${formatCurrency(total)}</span></div>
    `;
    itemsContainer.querySelectorAll('[data-remove-item]').forEach((button) => {
      button.addEventListener('click', (event) => {
        selectedItems.splice(Number(event.currentTarget.dataset.removeItem), 1);
        renderItems();
      });
    });
  };

  container.querySelector('#delivery-type').addEventListener('change', (event) => {
    const isDelivery = event.currentTarget.value === 'entrega';
    const addressField = container.querySelector('#address-field');
    addressField.hidden = !isDelivery;
    addressField.querySelector('input').required = isDelivery;
  });
  container.querySelector('#add-order-item')?.addEventListener('click', () => {
    const select = container.querySelector('#item-product');
    const product = products.find((item) => item.id === Number(select.value));
    const quantity = Number(container.querySelector('#item-quantity').value);
    if (!product || !Number.isInteger(quantity) || quantity < 1) {
      feedback = 'Selecione um produto e uma quantidade válida.';
      feedbackType = 'error';
      container.querySelector('#order-create-feedback').innerHTML = feedbackMarkup(feedback, feedbackType);
      return;
    }
    const existing = selectedItems.find((item) => item.produto_id === product.id);
    if (existing) existing.quantidade += quantity;
    else selectedItems.push({
      produto_id: product.id,
      nome: product.nome,
      preco_varejo: product.preco_varejo,
      quantidade: quantity,
    });
    feedback = '';
    container.querySelector('#order-create-feedback').innerHTML = '';
    select.value = '';
    container.querySelector('#item-quantity').value = '1';
    renderItems();
  });
  container.querySelector('#create-order-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!selectedItems.length) {
      feedback = 'O pedido precisa ter pelo menos um item.';
      container.querySelector('#order-create-feedback').innerHTML = feedbackMarkup(feedback);
      return;
    }

    const form = event.currentTarget;
    const values = new FormData(form);
    const isDelivery = values.get('tipo_entrega') === 'entrega';
    const submitButton = form.querySelector('button[type="submit"]');
    submitButton.disabled = true;
    try {
      const created = await api('/pedidos', {
        method: 'POST',
        body: {
          cliente_nome: String(values.get('cliente_nome')).trim(),
          cliente_email: String(values.get('cliente_email')).trim(),
          cliente_telefone: String(values.get('cliente_telefone')).trim(),
          data_entrega: values.get('data_entrega'),
          tipo_entrega: values.get('tipo_entrega'),
          endereco_entrega: isDelivery ? String(values.get('endereco_entrega')).trim() : null,
          observacoes: String(values.get('observacoes') || '').trim() || null,
          items: selectedItems.map(({ produto_id, quantidade }) => ({ produto_id, quantidade })),
        },
      });
      container.querySelector('#order-create-feedback').innerHTML = `
        ${feedbackMarkup(`Pedido ${created.numero_pedido} criado com sucesso.`, 'success')}
        <a class="button button--secondary" href="#/pedidos">Ir para pedidos</a>
      `;
      form.reset();
      selectedItems = [];
      renderItems();
    } catch (error) {
      container.querySelector('#order-create-feedback').innerHTML = feedbackMarkup(errorMessage(error));
    } finally {
      submitButton.disabled = false;
    }
  });

  renderItems();
}
