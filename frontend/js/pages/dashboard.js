import { api } from '../api.js';
import { getCurrentUser, hasAnyRole } from '../auth.js';
import {
  escapeHtml,
  formatCurrency,
  formatDateTime,
  formatNumber,
  statusClass,
  statusLabel,
} from '../common.js';

export async function render(container) {
  const canManage = hasAnyRole(['admin', 'gerente']);
  const [dashboard, stockAlerts] = await Promise.all([
    api('/dashboard/home'),
    canManage ? api('/estoque/alertas') : Promise.resolve([]),
  ]);

  const deliveries = dashboard.proximasEntregas || [];
  const ingredientPlan = dashboard.ingredientesNecessarios;
  const ingredientAlerts = ingredientPlan?.alertas || [];
  const user = getCurrentUser();
  const shortageById = new Map(
    ingredientAlerts.map((alert) => [alert.ingrediente_id, alert]),
  );

  container.innerHTML = `
    <section class="page-heading">
      <div>
        <h2>Buongiorno, ${escapeHtml(user?.nome || '')}!</h2>
        <p>Os pedidos e a fornada de hoje, em um só lugar.</p>
      </div>
      ${canManage ? '<a class="button button--primary" href="#/pedido-novo">Criar pedido</a>' : ''}
    </section>

    <section class="stats-grid" aria-label="Resumo da operação">
      <article class="stat-card">
        <span class="stat-label">Entregas nos próximos 7 dias</span>
        <strong class="stat-value">${deliveries.reduce((total, item) => total + item.total_pedidos, 0)}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">Ingredientes para a próxima produção</span>
        <strong class="stat-value">${ingredientPlan?.ingredientes?.length || 0}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">Faltas para a produção</span>
        <strong class="stat-value">${ingredientAlerts.length}</strong>
      </article>
      <article class="stat-card">
        <span class="stat-label">Alertas de estoque mínimo</span>
        <strong class="stat-value">${stockAlerts.length}</strong>
      </article>
    </section>

    <div class="dashboard-grid">
      <section class="panel">
        <div class="panel-heading">
          <div><h3>Próximas entregas</h3><p>Pedidos programados nos próximos sete dias.</p></div>
          ${canManage ? '<a class="link-button" href="#/pedidos">Ver pedidos</a>' : ''}
        </div>
        ${deliveries.length
          ? `<div class="list-cards">${deliveries.map((delivery) => `
              <article class="list-row">
                <div><strong>${formatDateTime(delivery.data)}</strong><small>${delivery.total_pedidos} pedido(s)</small></div>
                <span class="badge badge--${statusClass(delivery.status)}">${escapeHtml(statusLabel(delivery.status))}</span>
              </article>`).join('')}</div>`
          : '<div class="empty-state"><p>Nenhuma entrega programada para os próximos sete dias.</p></div>'}
      </section>

      <section class="panel">
        <div class="panel-heading"><div><h3>Estoque baixo</h3><p>Itens no mínimo ou abaixo dele.</p></div></div>
        ${stockAlerts.length
          ? `<div class="notice-list">${stockAlerts.slice(0, 5).map((alert) => `
              <article class="notice-item ${alert.status === 'crítico' ? 'notice-item--critical' : ''}">
                <strong>${escapeHtml(alert.ingrediente_nome)}</strong>
                <span>${formatNumber(alert.quantidade_atual)} ${escapeHtml(alert.unidade || '')} disponíveis · mínimo ${formatNumber(alert.quantidade_minima)}</span>
              </article>`).join('')}</div>
            <p><a class="link-button" href="#/estoque">Abrir estoque →</a></p>`
          : '<div class="empty-state"><p>Nenhum alerta de estoque no momento.</p></div>'}
      </section>
    </div>

    <section class="panel">
      <div class="panel-heading">
        <div>
          <h3>Ingredientes para a próxima produção</h3>
          <p>${ingredientPlan ? `Previsão para ${formatDateTime(ingredientPlan.data_entrega)}.` : 'Não há pedidos para a próxima data prevista.'}</p>
        </div>
        ${canManage ? '<a class="link-button" href="#/ingredientes">Ver ingredientes</a>' : ''}
      </div>
      ${ingredientPlan?.ingredientes?.length
        ? `<div class="data-table-wrap"><table class="data-table">
            <thead><tr><th>Ingrediente</th><th>Necessário</th><th>Disponibilidade</th></tr></thead>
            <tbody>${ingredientPlan.ingredientes.map((ingredient) => {
              const alert = shortageById.get(ingredient.id);
              return `<tr>
                <td>${escapeHtml(ingredient.nome)}</td>
                <td>${formatNumber(ingredient.quantidade)} ${escapeHtml(ingredient.unidade || '')}</td>
                <td>${alert
                  ? `<span class="badge badge--critical">Falta ${formatNumber(alert.diferenca)} ${escapeHtml(alert.unidade || '')}</span>`
                  : '<span class="badge badge--ok">Estoque suficiente</span>'}</td>
              </tr>`;
            }).join('')}</tbody>
          </table></div>`
        : '<div class="empty-state"><p>Quando houver pedidos para a próxima produção, os ingredientes serão calculados aqui.</p></div>'}
    </section>
  `;
}
