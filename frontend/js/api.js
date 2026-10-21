const apiBaseUrl = window.tuiaConfig?.apiBaseUrl?.replace(/\/+$/, '');

if (!apiBaseUrl) {
  throw new Error('A configuração da API não foi carregada.');
}

export class ApiError extends Error {
  constructor(message, status, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

let refreshPromise = null;

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = fetch(`${apiBaseUrl}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
      .then((response) => {
        if (response.status === 401) return false;
        if (!response.ok) {
          throw new ApiError('Falha ao renovar a sessão.', response.status);
        }
        return true;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

async function parseResponse(response) {
  if (response.status === 204) return null;

  const text = await response.text();
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

async function send(path, options, canRefresh) {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  const headers = new Headers(options.headers || {});
  const requestOptions = {
    method: options.method || 'GET',
    credentials: 'include',
    headers,
  };

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
    requestOptions.body = JSON.stringify(options.body);
  }

  let response = await fetch(`${apiBaseUrl}${normalizedPath}`, requestOptions);

  const isLoginOrTokenEndpoint = [
    '/auth/login',
    '/auth/refresh',
    '/auth/logout',
  ].includes(normalizedPath);
  if (response.status === 401 && canRefresh && !isLoginOrTokenEndpoint) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      response = await fetch(`${apiBaseUrl}${normalizedPath}`, requestOptions);
    } else {
      window.dispatchEvent(new Event('tuia:session-expired'));
    }
  }

  const data = await parseResponse(response);
  if (!response.ok) {
    const detail = data?.detail;
    const message = typeof detail === 'string'
      ? detail
      : 'A API recusou a solicitação.';
    throw new ApiError(message, response.status, detail);
  }

  return data;
}

export function api(path, options = {}) {
  return send(path, options, true);
}
