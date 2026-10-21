export function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[character]);
}

export function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(Number(value) || 0);
}

export function formatNumber(value, maximumFractionDigits = 2) {
  return new Intl.NumberFormat('pt-BR', { maximumFractionDigits }).format(
    Number(value) || 0,
  );
}

export function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? '—'
    : new Intl.DateTimeFormat('pt-BR', {
        weekday: 'short',
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      }).format(date);
}

export function formatDateTime(value) {
  if (!value) return '—';
  const date = new Date(value);
  return Number.isNaN(date.valueOf())
    ? '—'
    : new Intl.DateTimeFormat('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      }).format(date);
}

export function errorMessage(error) {
  const detail = error?.detail ?? error?.message;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg || item.message || String(item))
      .join('; ');
  }
  return typeof detail === 'string' && detail
    ? detail
    : 'Não foi possível concluir a operação.';
}

export function feedbackMarkup(message = '', type = 'error') {
  return message
    ? `<div class="notice notice--${type}" role="status">${escapeHtml(message)}</div>`
    : '';
}

export function statusLabel(status) {
  return ({
    pendente: 'Pendente',
    confirmado: 'Confirmado',
    produção: 'Em produção',
    pronto: 'Pronto',
    entregue: 'Entregue',
    cancelado: 'Cancelado',
  })[status] || status || '—';
}

export function statusClass(status) {
  return ({
    pendente: 'pending',
    confirmado: 'confirmed',
    produção: 'production',
    pronto: 'ready',
    entregue: 'delivered',
    cancelado: 'cancelled',
  })[status] || 'neutral';
}
