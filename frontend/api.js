/**
 * CHORD - Central API Client & Authentication Manager
 * Connects frontend views with Django REST Backend
 */

function resolveApiBaseUrl() {
  if (typeof window !== 'undefined') {
    if (window.__ENV__ && window.__ENV__.VITE_API_URL) {
      return window.__ENV__.VITE_API_URL.replace(/\/+$/, '');
    }
    if (window.CHORD_API_URL) {
      return window.CHORD_API_URL.replace(/\/+$/, '');
    }
    const localOverride = localStorage.getItem('chord_api_url');
    if (localOverride) {
      return localOverride.replace(/\/+$/, '');
    }
  }
  if (typeof process !== 'undefined' && process.env) {
    const envUrl = process.env.VITE_API_URL || process.env.REACT_APP_API_URL || process.env.CHORD_API_URL;
    if (envUrl) return envUrl.replace(/\/+$/, '');
  }
  return 'http://127.0.0.1:8000/api';
}

const api = {
  get baseUrl() {
    return resolveApiBaseUrl();
  },

  // Token & Auth Storage Keys
  TOKEN_KEY: 'chord_auth_token',
  USER_KEY: 'chord_auth_user',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY) || '';
  },

  setToken(token) {
    if (token) {
      localStorage.setItem(this.TOKEN_KEY, token);
    } else {
      localStorage.removeItem(this.TOKEN_KEY);
    }
  },

  getUser() {
    try {
      const raw = localStorage.getItem(this.USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },

  setUser(user) {
    if (user) {
      localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.USER_KEY);
    }
  },

  getRole() {
    const u = this.getUser();
    return u?.role || 'citizen';
  },

  logout() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    window.location.href = 'login.html';
  },

  getHeaders(isMultipart = false) {
    const headers = {};
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
      headers['Accept'] = 'application/json';
    }
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const user = this.getUser();
    if (user?.email) {
      headers['X-User-Email'] = user.email;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;
    const headers = { ...this.getHeaders(options.isMultipart), ...(options.headers || {}) };

    const config = {
      method: options.method || 'GET',
      headers: headers,
      ...options
    };

    if (options.body && !options.isMultipart && typeof options.body === 'object') {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.message || `HTTP Error ${response.status}`);
      }
      return data;
    } catch (error) {
      console.warn(`[CHORD API Warning] ${config.method} ${endpoint}:`, error.message);
      throw error;
    }
  },

  async get(endpoint, params = {}) {
    let query = '';
    if (params && Object.keys(params).length > 0) {
      const sp = new URLSearchParams();
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') sp.append(k, v);
      });
      const qs = sp.toString();
      if (qs) query = (endpoint.includes('?') ? '&' : '?') + qs;
    }
    return this.request(`${endpoint}${query}`, { method: 'GET' });
  },

  async post(endpoint, body = {}) {
    return this.request(endpoint, { method: 'POST', body });
  },

  async put(endpoint, body = {}) {
    return this.request(endpoint, { method: 'PUT', body });
  },

  async patch(endpoint, body = {}) {
    return this.request(endpoint, { method: 'PATCH', body });
  },

  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  async upload(endpoint, formData) {
    return this.request(endpoint, {
      method: 'POST',
      body: formData,
      isMultipart: true
    });
  },

  // Global Toast Helper
  toast(msg, type = 'info') {
    let toastEl = document.getElementById('toast') || document.getElementById('toastBox');
    let toastMsg = document.getElementById('toastMsg') || toastEl;
    if (toastEl) {
      if (toastMsg && toastMsg !== toastEl) {
        toastMsg.textContent = msg;
      } else {
        toastEl.textContent = msg;
      }
      toastEl.classList.add('show');
      setTimeout(() => toastEl.classList.remove('show'), 2800);
    } else {
      console.log(`[Toast] ${msg}`);
    }
  }
};

// Make available globally
window.api = api;
