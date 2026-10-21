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
    const ingredients = await api('/ingredientes');
    container.innerHTML = `
      <section class="page-heading">
        <div><h2>Ingredientes</h2><p>Organize insumos, unidades e custos de referência.</p></div>
      </section>
      ${feedbackMarkup(feedback, feedbackType)}
      <section class="panel">
        <div class="panel-heading"><div><h3>${editing ? 'Editar ingrediente' : 'Novo ingrediente'}</h3><p>O estoque inicial do novo ingrediente será zero.</p></div></div>
        <form id="ingredient-form">
          <div class="form-grid">
            <div class="field"><label for="ingredient-name">Nome</label><input id="ingredient-name" name="nome" required minlength="3" value="${escapeHtml(editing?.nome || '')}"></div>
            <div class="field"><label for="ingredient-unit">Unidade</label><input id="ingredient-unit" name="unidade" list="unit-options" required value="${escapeHtml(editing?.unidade || '')}"><datalist id="unit-options"><option value="kg"><option value="g"><option value="L"><option value="ml"><option value="un"><option value="dúzia"></datalist></div>
            <div class="field"><label for="ingredient-price">Preço unitário</label><input id="ingredient-price" name="preco_unitario" type="number" min="0" step="0.01" required value="${editing?.preco_unitario != null ? escapeHtml(editing.preco_unitario) : ''}"></div>
          </div>
          <div class="form-actions">
            <button class="button button--primary" type="submit">${editing ? 'Salvar alterações' : 'Cadastrar ingrediente'}</button>
            ${editing ? '<button class="button button--quiet" id="cancel-ingredient-edit" type="button">Cancelar edição</button>' : ''}
          </div>
        </form>
      </section>
      <section class="panel">
        <div class="panel-heading"><div><h3>Insumos cadastrados</h3><p>${ingredients.length} ingrediente(s)</p></div></div>
        ${ingredients.length ? `<div class="data-table-wrap"><table class="data-table">
          <thead><tr><th>Ingrediente</th><th>Unidade</th><th>Preço unitário</th><th>Ações</th></tr></thead>
          <tbody>${ingredients.map((ingredient) => `<tr>
            <td><strong>${escapeHtml(ingredient.nome)}</strong></td>
            <td>${escapeHtml(ingredient.unidade || '—')}</td>
            <td>${ingredient.preco_unitario == null ? '—' : formatCurrency(ingredient.preco_unitario)}</td>
            <td><div class="table-actions">
              <button class="button button--secondary button--small" type="button" data-edit-ingredient="${ingredient.id}">Editar</button>
              <button class="button button--danger button--small" type="button" data-delete-ingredient="${ingredient.id}">Excluir</button>
            </div></td>
          </tr>`).join('')}</tbody>
        </table></div>` : '<div class="empty-state"><p>Nenhum ingrediente cadastrado.</p></div>'}
      </section>
    `;

    container.querySelector('#ingredient-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const values = new FormData(event.currentTarget);
      const payload = {
        nome: String(values.get('nome')).trim(),
        unidade: String(values.get('unidade')).trim(),
        preco_unitario: Number(values.get('preco_unitario')),
      };
      const submit = event.currentTarget.querySelector('button[type="submit"]');
      submit.disabled = true;
      try {
        if (editing) {
          await api(`/ingredientes/${editing.id}`, { method: 'PUT', body: payload });
          feedback = 'Ingrediente atualizado.';
        } else {
          await api('/ingredientes', { method: 'POST', body: payload });
          feedback = 'Ingrediente cadastrado com estoque inicial zerado.';
        }
        editing = null;
        feedbackType = 'success';
      } catch (error) {
        feedback = errorMessage(error);
        feedbackType = 'error';
      }
      await draw();
    });

    container.querySelector('#cancel-ingredient-edit')?.addEventListener('click', () => {
      editing = null;
      feedback = '';
      void draw();
    });
    container.querySelectorAll('[data-edit-ingredient]').forEach((button) => {
      button.addEventListener('click', () => {
        editing = ingredients.find((ingredient) => ingredient.id === Number(button.dataset.editIngredient));
        feedback = '';
        void draw();
      });
    });
    container.querySelectorAll('[data-delete-ingredient]').forEach((button) => {
      button.addEventListener('click', async () => {
        if (!window.confirm('Excluir este ingrediente? Ele também pode estar ligado a receitas.')) return;
        try {
          await api(`/ingredientes/${button.dataset.deleteIngredient}`, { method: 'DELETE' });
          feedback = 'Ingrediente excluído.';
          feedbackType = 'success';
          if (editing?.id === Number(button.dataset.deleteIngredient)) editing = null;
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
