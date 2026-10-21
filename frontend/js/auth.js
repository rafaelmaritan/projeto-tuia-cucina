import { api, ApiError } from './api.js';

let currentUser = null;

export function getCurrentUser() {
  return currentUser;
}

export function setCurrentUser(user) {
  currentUser = user;
}

export function hasAnyRole(roles) {
  return Boolean(currentUser && roles.includes(currentUser.papel));
}

export async function initializeAuth() {
  try {
    currentUser = await api('/auth/me');
    return currentUser;
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      currentUser = null;
      return null;
    }
    throw error;
  }
}

export async function login(email, senha) {
  await api('/auth/login', {
    method: 'POST',
    body: { email, senha },
  });
  currentUser = await api('/auth/me');
  return currentUser;
}

export async function logout() {
  try {
    await api('/auth/logout', { method: 'POST', body: {} });
  } finally {
    currentUser = null;
  }
}
