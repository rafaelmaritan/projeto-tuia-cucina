import { api } from '../api.js';
import { hasAnyRole } from '../auth.js';
import {
  errorMessage,
  escapeHtml,
  feedbackMarkup,
  formatNumber,
} from '../common.js';

export async function render(container) {
  const canEdit = hasAnyRole(['admin', 'gerente']);
  let recipes = [];
  let products = [];
  let ingredients = [];
  let editing = null;
  let feedback = '';
  let feedbackType = 'success';

  async function loadData() {
    if (canEdit) {
      [recipes, products, ingredients] = await Promise.all([
        api('/receitas'),
        api('/produtos'),
        api('/ingredientes'),
      ]);
    } else {
      recipes = await api('/receitas');
      products = [];
      ingredients = [];
    }
  }

  function ingredientOptions(selectedId = '') {
    return `<option value="">Selecione um ingrediente</option>${ingredients.map((ingredient) => `
      <option value="${ingredient.id}" ${Number(selectedId) === ingredient.id ? 'selected' : ''}>
        ${escapeHtml(ingredient.nome)}${ingredient.unidade ? ` (${escapeHtml(ingredient.unidade)})` : ''}
      </option>`).join('')}`;
  }

  function addIngredientRow(list, value = null) {
    const row = document.createElement('div');
    row.className = 'ingredient-row';
    row.dataset.ingredientRow = '';
    row.innerHTML = `
      <div class="field"><label>Ingrediente</label><select name="ingrediente_id" required>${ingredientOptions(value?.ingrediente_id || '')}</select></div>
      <div class="field"><label>Quantidade por lote</label><input name="quantidade" type="number" min="0.01" step="any" required value="${value ? escapeHtml(value.quantidade) : ''}"></div>
      <button class="button button--danger button--small" type="button" data-remove-ingredient>Remover</button>
    `;
    row.querySelector('[data-remove-ingredient]').addEventListener('click', () => row.remove());
    list.append(row);
  }

  async function draw() {
    await loadData();
    const productById = new Map(products.map((product) => [product.id, product]));

    container.innerHTML = `
      <section class="page-heading">
        <div><h2>Receitas</h2><p>Consulte lotes, ingredientes e instruções de preparo.</p></div>
        ${canEdit ? '<button class="button button--primary" id="new-recipe" type="button">Nova receita</button>' : ''}
      </section>
      ${feedbackMarkup(feedback, feedbackType)}
      ${canEdit ? `
        <section class="panel" id="recipe-editor">
          <div class="panel-heading"><div><h3>${editing ? 'Editar receita' : 'Cadastrar receita'}</h3><p>As quantidades de ingredientes correspondem ao lote informado.</p></div></div>
          ${products.length && ingredients.length ? `
            <form id="recipe-form">
              <div class="form-grid">
                <div class="field"><label for="recipe-name">Nome da receita</label><input id="recipe-name" name="nome" required value="${escapeHtml(editing?.nome || '')}"></div>
                ${editing
                  ? `<div class="field"><label>Produto</label><input value="${escapeHtml(productById.get(editing.produto_id)?.nome || `Produto ${editing.produto_id}`)}" disabled></div>`
                  : `<div class="field"><label for="recipe-product">Produto</label><select id="recipe-product" name="produto_id" required><option value="">Selecione um produto</option>${products.map((product) => `<option value="${product.id}">${escapeHtml(product.nome)}</option>`).join('')}</select></div>`}
                <div class="field"><label for="recipe-base">Rendimento do lote</label><input id="recipe-base" name="quantidade_base" type="number" min="1" step="1" required value="${editing ? escapeHtml(editing.quantidade_base || '') : ''}"></div>
                <div class="field"><label for="recipe-fermentation">Fermentação (horas)</label><input id="recipe-fermentation" name="tempo_fermentacao_horas" type="number" min="0" step="1" value="${editing?.tempo_fermentacao_horas ?? ''}"></div>
                <div class="field"><label for="recipe-baking">Assamento (minutos)</label><input id="recipe-baking" name="tempo_assamento_minutos" type="number" min="0" step="1" value="${editing?.tempo_assamento_minutos ?? ''}"></div>
                <div class="field field--wide"><label for="recipe-instructions">Instruções</label><textarea id="recipe-instructions" name="instrucoes" rows="4">${escapeHtml(editing?.instrucoes || '')}</textarea></div>
              </div>
              <div class="panel panel--nested">
                <div class="panel-heading"><div><h3>Ingredientes do lote</h3><p>Use as unidades cadastradas em cada ingrediente.</p></div><button class="button button--secondary button--small" id="add-recipe-ingredient" type="button">Adicionar ingrediente</button></div>
                <div id="recipe-ingredients"></div>
              </div>
              <div class="form-actions">
                <button class="button button--primary" type="submit">${editing ? 'Salvar receita' : 'Cadastrar receita'}</button>
                ${editing ? '<button class="button button--quiet" id="cancel-recipe-edit" type="button">Cancelar edição</button>' : ''}
              </div>
            </form>
          ` : '<div class="empty-state"><p>Cadastre ao menos um produto e um ingrediente antes de criar uma receita.</p></div>'}
        </section>` : ''}
      <section class="panel">
        <div class="panel-heading"><div><h3>Receitas cadastradas</h3><p>${recipes.length} receita(s)</p></div></div>
        ${recipes.length ? `<div class="list-cards">${recipes.map((recipe) => {
          const productName = productById.get(recipe.produto_id)?.nome || `Produto ${recipe.produto_id}`;
          return `<details class="recipe-details">
            <summary class="list-row">
              <span><strong>${escapeHtml(recipe.nome)}</strong><small>${escapeHtml(productName)} · lote para ${formatNumber(recipe.quantidade_base || 0, 0)}</small></span>
              <span class="badge">${recipe.ingredientes?.length || 0} ingrediente(s)</span>
            </summary>
            <div class="detail-content">
              <p><strong>Fermentação:</strong> ${recipe.tempo_fermentacao_horas ?? 0} h · <strong>Assamento:</strong> ${recipe.tempo_assamento_minutos ?? 0} min</p>
              <div class="pill-list">${(recipe.ingredientes || []).map((item) => `
                <span class="ingredient-pill">${escapeHtml(item.ingrediente?.nome || `Ingrediente ${item.ingrediente_id}`)} · ${formatNumber(item.quantidade)} ${escapeHtml(item.ingrediente?.unidade || '')}</span>
              `).join('') || '<span class="help-text">Sem ingredientes vinculados.</span>'}</div>
              ${recipe.instrucoes ? `<p class="recipe-instructions">${escapeHtml(recipe.instrucoes).replace(/\n/g, '<br>')}</p>` : ''}
              ${canEdit ? `<div class="form-actions">
                <button class="button button--secondary button--small" type="button" data-edit-recipe="${recipe.id}">Editar</button>
                <button class="button button--danger button--small" type="button" data-delete-recipe="${recipe.id}">Excluir</button>
              </div>` : ''}
            </div>
          </details>`;
        }).join('')}</div>` : '<div class="empty-state"><p>Nenhuma receita cadastrada.</p></div>'}
      </section>
    `;

    if (!canEdit || !products.length || !ingredients.length) return;

    const ingredientList = container.querySelector('#recipe-ingredients');
    if (editing?.ingredientes?.length) {
      editing.ingredientes.forEach((item) => addIngredientRow(ingredientList, item));
    } else if (editing) {
      addIngredientRow(ingredientList);
    }

    container.querySelector('#new-recipe').addEventListener('click', () => {
      editing = null;
      feedback = '';
      void draw();
      container.querySelector('#recipe-editor')?.scrollIntoView({ behavior: 'smooth' });
    });
    container.querySelector('#add-recipe-ingredient').addEventListener('click', () => {
      addIngredientRow(ingredientList);
    });
    container.querySelector('#cancel-recipe-edit')?.addEventListener('click', () => {
      editing = null;
      feedback = '';
      void draw();
    });
    container.querySelector('#recipe-form')?.addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const formData = new FormData(form);
      const recipeIngredients = [...ingredientList.querySelectorAll('[data-ingredient-row]')].map((row) => ({
        ingrediente_id: Number(row.querySelector('[name="ingrediente_id"]').value),
        quantidade: Number(row.querySelector('[name="quantidade"]').value),
      }));
      if (!recipeIngredients.length || recipeIngredients.some((item) => !item.ingrediente_id || item.quantidade <= 0)) {
        feedback = 'Adicione pelo menos um ingrediente com quantidade válida.';
        feedbackType = 'error';
        await draw();
        return;
      }

      const payload = {
        nome: String(formData.get('nome')).trim(),
        quantidade_base: Number(formData.get('quantidade_base')),
        tempo_fermentacao_horas: formData.get('tempo_fermentacao_horas') === '' ? null : Number(formData.get('tempo_fermentacao_horas')),
        tempo_assamento_minutos: formData.get('tempo_assamento_minutos') === '' ? null : Number(formData.get('tempo_assamento_minutos')),
        instrucoes: String(formData.get('instrucoes') || '').trim() || null,
        ingredientes: recipeIngredients,
      };
      if (!editing) payload.produto_id = Number(formData.get('produto_id'));

      const submit = form.querySelector('button[type="submit"]');
      submit.disabled = true;
      try {
        if (editing) {
          await api(`/receitas/${editing.id}`, { method: 'PUT', body: payload });
          feedback = 'Receita atualizada.';
        } else {
          await api('/receitas', { method: 'POST', body: payload });
          feedback = 'Receita cadastrada.';
        }
        editing = null;
        feedbackType = 'success';
      } catch (error) {
        feedback = errorMessage(error);
        feedbackType = 'error';
      }
      await draw();
    });
    container.querySelectorAll('[data-edit-recipe]').forEach((button) => {
      button.addEventListener('click', () => {
        editing = recipes.find((recipe) => recipe.id === Number(button.dataset.editRecipe));
        feedback = '';
        void draw();
        container.querySelector('#recipe-editor')?.scrollIntoView({ behavior: 'smooth' });
      });
    });
    container.querySelectorAll('[data-delete-recipe]').forEach((button) => {
      button.addEventListener('click', async () => {
        if (!window.confirm('Excluir esta receita?')) return;
        try {
          await api(`/receitas/${button.dataset.deleteRecipe}`, { method: 'DELETE' });
          feedback = 'Receita excluída.';
          feedbackType = 'success';
          if (editing?.id === Number(button.dataset.deleteRecipe)) editing = null;
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
