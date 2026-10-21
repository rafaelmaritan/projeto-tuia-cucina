import { api } from '../api.js';
import {
  errorMessage,
  escapeHtml,
  feedbackMarkup,
  formatCurrency,
} from '../common.js';

export async function render(container) {
  let editing = null;
  let feedback = '';
  let feedbackType = 'success';

  async function draw() {
    const products = await api('/produtos');
    container.innerHTML = `
      <section class="page-heading">
        <div><h2>Catálogo de produtos</h2><p>Gerencie preços, custos e os itens disponíveis para pedidos.</p></div>
      </section>
      ${feedbackMarkup(feedback, feedbackType)}
      <section class="panel">
        <div class="panel-heading"><div><h3>${editing ? 'Editar produto' : 'Novo produto'}</h3><p>O preço de venda é usado no cálculo dos pedidos.</p></div></div>
        <form id="product-form">
          <div class="form-grid">
            <div class="field"><label for="product-name">Nome</label><input id="product-name" name="nome" required minlength="3" value="${escapeHtml(editing?.nome || '')}"></div>
            <div class="field"><label for="product-price">Preço de venda (R$)</label><input id="product-price" name="preco_varejo" type="number" min="0.01" step="0.01" required value="${editing ? escapeHtml(editing.preco_varejo) : ''}"></div>
            <div class="field"><label for="product-cost">Custo estimado (R$)</label><input id="product-cost" name="preco_custo" type="number" min="0" step="0.01" value="${editing?.preco_custo != null ? escapeHtml(editing.preco_custo) : ''}"></div>
            <div class="field field--wide"><label for="product-description">Descrição</label><textarea id="product-description" name="descricao" rows="2">${escapeHtml(editing?.descricao || '')}</textarea></div>
          </div>
          <div class="form-actions">
            <button class="button button--primary" type="submit">${editing ? 'Salvar alterações' : 'Cadastrar produto'}</button>
            ${editing ? '<button class="button button--quiet" id="cancel-product-edit" type="button">Cancelar edição</button>' : ''}
          </div>
        </form>
      </section>
      <section class="panel">
        <div class="panel-heading"><div><h3>Produtos cadastrados</h3><p>${products.length} produto(s)</p></div></div>
        ${products.length ? `<div class="data-table-wrap"><table class="data-table">
          <thead><tr><th>Produto</th><th>Preço de venda</th><th>Custo</th><th>Margem estimada</th><th>Ações</th></tr></thead>
          <tbody>${products.map((product) => {
            const margin = product.preco_custo > 0
              ? ((product.preco_varejo - product.preco_custo) / product.preco_varejo) * 100
              : null;
            return `<tr>
              <td><strong>${escapeHtml(product.nome)}</strong><small class="table-secondary">${escapeHtml(product.descricao || '')}</small></td>
              <td>${formatCurrency(product.preco_varejo)}</td>
              <td>${product.preco_custo == null ? '—' : formatCurrency(product.preco_custo)}</td>
              <td>${margin == null ? '—' : `${margin.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`}</td>
              <td><div class="table-actions">
                <button class="button button--secondary button--small" type="button" data-edit-product="${product.id}">Editar</button>
                <button class="button button--danger button--small" type="button" data-delete-product="${product.id}">Excluir</button>
              </div></td>
            </tr>`;
          }).join('')}</tbody>
        </table></div>` : '<div class="empty-state"><p>Nenhum produto cadastrado.</p></div>'}
      </section>
    `;

    container.querySelector('#product-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const values = new FormData(event.currentTarget);
      const payload = {
        nome: String(values.get('nome')).trim(),
        descricao: String(values.get('descricao') || '').trim() || null,
        preco_varejo: Number(values.get('preco_varejo')),
        preco_custo: values.get('preco_custo') === '' ? null : Number(values.get('preco_custo')),
      };
      const submit = event.currentTarget.querySelector('button[type="submit"]');
      submit.disabled = true;
      try {
        if (editing) {
          await api(`/produtos/${editing.id}`, { method: 'PUT', body: payload });
          feedback = 'Produto atualizado.';
        } else {
          await api('/produtos', { method: 'POST', body: payload });
          feedback = 'Produto cadastrado.';
        }
        feedbackType = 'success';
        editing = null;
      } catch (error) {
        feedback = errorMessage(error);
        feedbackType = 'error';
      }
      await draw();
    });

    container.querySelector('#cancel-product-edit')?.addEventListener('click', () => {
      editing = null;
      feedback = '';
      void draw();
    });
    container.querySelectorAll('[data-edit-product]').forEach((button) => {
      button.addEventListener('click', () => {
        editing = products.find((product) => product.id === Number(button.dataset.editProduct));
        feedback = '';
        void draw();
        container.querySelector('#product-name')?.focus();
      });
    });
    container.querySelectorAll('[data-delete-product]').forEach((button) => {
      button.addEventListener('click', async () => {
        if (!window.confirm('Excluir este produto?')) return;
        try {
          await api(`/produtos/${button.dataset.deleteProduct}`, { method: 'DELETE' });
          feedback = 'Produto excluído.';
          feedbackType = 'success';
          if (editing?.id === Number(button.dataset.deleteProduct)) editing = null;
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
