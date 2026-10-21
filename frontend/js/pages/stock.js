import { api } from '../api.js';
import {
  errorMessage,
  escapeHtml,
  feedbackMarkup,
  formatDateTime,
  formatNumber,
} from '../common.js';

export async function render(container) {
  let feedback = '';
  let feedbackType = 'success';

  async function draw() {
    const [stocks, ingredients, alerts] = await Promise.all([
      api('/estoque'),
      api('/ingredientes'),
      api('/estoque/alertas'),
    ]);
    const ingredientById = new Map(ingredients.map((item) => [item.id, item]));
    const alertById = new Map(alerts.map((item) => [item.ingrediente_id, item]));

    container.innerHTML = `
      <section class="page-heading">
        <div><h2>Estoque de ingredientes</h2><p>Registre entradas, consumo e ajustes com histórico.</p></div>
      </section>
      ${feedbackMarkup(feedback, feedbackType)}
      <section class="panel">
        <div class="panel-heading"><div><h3>Posição atual</h3><p>${stocks.length} item(ns) com controle de estoque</p></div></div>
        ${stocks.length ? `<div class="data-table-wrap"><table class="data-table">
          <thead><tr><th>Ingrediente</th><th>Disponível</th><th>Mínimo</th><th>Situação</th><th>Atualizado</th><th>Ações</th></tr></thead>
          <tbody>${stocks.map((stock) => {
            const ingredient = ingredientById.get(stock.ingrediente_id);
            const alert = alertById.get(stock.ingrediente_id);
            const status = alert?.status || 'ok';
            return `<tr>
              <td><strong>${escapeHtml(ingredient?.nome || `Ingrediente ${stock.ingrediente_id}`)}</strong></td>
              <td>${formatNumber(stock.quantidade)} ${escapeHtml(ingredient?.unidade || '')}</td>
              <td>${formatNumber(stock.quantidade_minima)} ${escapeHtml(ingredient?.unidade || '')}</td>
              <td><span class="badge badge--${status === 'crítico' ? 'critical' : status === 'baixo' ? 'low' : 'ok'}">${status === 'crítico' ? 'Crítico' : status === 'baixo' ? 'Baixo' : 'OK'}</span></td>
              <td>${formatDateTime(stock.atualizado_em)}</td>
              <td><div class="table-actions">
                <button class="button button--secondary button--small" type="button" data-stock-history="${stock.id}">Histórico</button>
                <button class="button button--secondary button--small" type="button" data-stock-min="${stock.id}">Definir mínimo</button>
              </div></td>
            </tr>
            <tr class="detail-row"><td colspan="6">
              <form class="inline-form stock-movement-form" data-stock-movement="${stock.id}">
                <div class="field"><label>Movimento</label><select name="tipo" required><option value="entrada">Entrada</option><option value="saída">Saída</option><option value="ajuste">Ajuste para quantidade</option></select></div>
                <div class="field"><label>Quantidade</label><input name="quantidade" type="number" min="0.01" step="any" required></div>
                <div class="field"><label>Observação</label><input name="observacao" maxlength="1000" placeholder="Opcional"></div>
                <button class="button button--primary button--small" type="submit">Registrar</button>
              </form>
              <div class="history-content" id="history-${stock.id}" hidden></div>
            </td></tr>`;
          }).join('')}</tbody>
        </table></div>` : '<div class="empty-state"><p>Não há registros de estoque. Cadastre um ingrediente para iniciar.</p></div>'}
      </section>
      ${alerts.length ? `<section class="panel">
        <div class="panel-heading"><div><h3>Alertas</h3><p>Ingredientes que atingiram o estoque mínimo.</p></div></div>
        <div class="notice-list">${alerts.map((alert) => `<article class="notice-item ${alert.status === 'crítico' ? 'notice-item--critical' : ''}">
          <strong>${escapeHtml(alert.ingrediente_nome)} · ${alert.status === 'crítico' ? 'Crítico' : 'Baixo'}</strong>
          <span>${formatNumber(alert.quantidade_atual)} ${escapeHtml(alert.unidade || '')} disponíveis; mínimo ${formatNumber(alert.quantidade_minima)} ${escapeHtml(alert.unidade || '')}.</span>
        </article>`).join('')}</div>
      </section>` : ''}
    `;

    container.querySelectorAll('[data-stock-movement]').forEach((form) => {
      form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const values = new FormData(event.currentTarget);
        const submit = event.currentTarget.querySelector('button[type="submit"]');
        submit.disabled = true;
        try {
          await api(`/estoque/${event.currentTarget.dataset.stockMovement}/movimento`, {
            method: 'POST',
            body: {
              tipo: values.get('tipo'),
              quantidade: Number(values.get('quantidade')),
              observacao: String(values.get('observacao') || '').trim() || null,
            },
          });
          feedback = 'Movimento registrado.';
          feedbackType = 'success';
        } catch (error) {
          feedback = errorMessage(error);
          feedbackType = 'error';
        }
        await draw();
      });
    });

    container.querySelectorAll('[data-stock-history]').forEach((button) => {
      button.addEventListener('click', async () => {
        const stockId = button.dataset.stockHistory;
        const historyContainer = container.querySelector(`#history-${stockId}`);
        if (!historyContainer.hidden) {
          historyContainer.hidden = true;
          return;
        }
        historyContainer.hidden = false;
        historyContainer.innerHTML = '<p class="help-text">Carregando histórico…</p>';
        try {
          const history = await api(`/estoque/${stockId}/historico?limit=50`);
          historyContainer.innerHTML = history.length
            ? `<div class="data-table-wrap"><table class="data-table">
                <thead><tr><th>Data</th><th>Tipo</th><th>Quantidade</th><th>Observação</th></tr></thead>
                <tbody>${history.map((movement) => `<tr>
                  <td>${formatDateTime(movement.criado_em)}</td>
                  <td>${escapeHtml(movement.tipo)}</td>
                  <td>${formatNumber(movement.quantidade)}</td>
                  <td>${escapeHtml(movement.observacao || '—')}</td>
                </tr>`).join('')}</tbody></table></div>`
            : '<p class="help-text">Ainda não há movimentos registrados.</p>';
        } catch (error) {
          historyContainer.innerHTML = feedbackMarkup(errorMessage(error));
        }
      });
    });

    container.querySelectorAll('[data-stock-min]').forEach((button) => {
      button.addEventListener('click', async () => {
        const stock = stocks.find((item) => item.id === Number(button.dataset.stockMin));
        const ingredient = ingredientById.get(stock.ingrediente_id);
        const value = window.prompt(
          `Novo mínimo para ${ingredient?.nome || 'ingrediente'}:`,
          String(stock.quantidade_minima),
        );
        if (value === null || value.trim() === '') return;
        const minimum = Number(value.replace(',', '.'));
        if (!Number.isFinite(minimum) || minimum < 0) {
          feedback = 'Informe uma quantidade mínima válida, igual ou maior que zero.';
          feedbackType = 'error';
          await draw();
          return;
        }
        try {
          await api(`/estoque/${stock.id}/quantidade-minima`, {
            method: 'PUT',
            body: { quantidade_minima: minimum },
          });
          feedback = 'Quantidade mínima atualizada.';
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
