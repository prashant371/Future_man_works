/**
 * API Service Layer
 *
 * Centralized HTTP client for communicating with the FastAPI backend.
 * Handles auth tokens, error formatting, and request/response flow.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseUrl = API_BASE;
  }

  /**
   * Get the stored auth token.
   */
  getToken() {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  /**
   * Get the stored refresh token.
   */
  getRefreshToken() {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('refresh_token');
  }

  /**
   * Store auth tokens.
   */
  setTokens(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  /**
   * Clear stored tokens.
   */
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  /**
   * Build headers for a request.
   */
  getHeaders(authenticated = true) {
    const headers = { 'Content-Type': 'application/json' };
    if (authenticated) {
      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return headers;
  }

  /**
   * Core request method with error handling and token refresh.
   */
  async request(method, path, body = null, authenticated = true) {
    const url = `${this.baseUrl}${path}`;
    const options = {
      method,
      headers: this.getHeaders(authenticated),
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    let response = await fetch(url, options);

    // If 401, try to refresh the token
    if (response.status === 401 && authenticated) {
      const refreshed = await this.refreshAccessToken();
      if (refreshed) {
        options.headers = this.getHeaders(true);
        response = await fetch(url, options);
      } else {
        this.clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Session expired. Please log in again.');
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const message = errorData.detail || `Request failed (${response.status})`;
      throw new Error(message);
    }

    // Handle 204 No Content
    if (response.status === 204) return null;

    return response.json();
  }

  /**
   * Attempt to refresh the access token.
   */
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // ── Auth ────────────────────────────────────────────────
  async register(email, name, password) {
    const data = await this.request('POST', '/api/auth/register', { email, name, password }, false);
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async login(email, password) {
    const data = await this.request('POST', '/api/auth/login', { email, password }, false);
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async logout() {
    await this.request('POST', '/api/auth/logout').catch(() => {});
    this.clearTokens();
  }

  async getMe() {
    return this.request('GET', '/api/auth/me');
  }

  // ── Chat ────────────────────────────────────────────────
  async sendMessage(message, conversationId = null) {
    return this.request('POST', '/api/chat', {
      message,
      conversation_id: conversationId,
    });
  }

  async getConversations() {
    return this.request('GET', '/api/conversations');
  }

  async getConversation(id) {
    return this.request('GET', `/api/conversations/${id}`);
  }

  async createConversation() {
    return this.request('POST', '/api/conversations');
  }

  async deleteConversation(id) {
    return this.request('DELETE', `/api/conversations/${id}`);
  }

  // ── Connections ─────────────────────────────────────────
  async getConnections() {
    return this.request('GET', '/api/connections');
  }

  async connectPlatform(platform) {
    return this.request('POST', `/api/connections/${platform}/connect`);
  }

  async disconnectPlatform(platform) {
    return this.request('DELETE', `/api/connections/${platform}`);
  }

  // ── Tasks / Activity ───────────────────────────────────
  async getTasks(limit = 50, offset = 0) {
    return this.request('GET', `/api/tasks?limit=${limit}&offset=${offset}`);
  }

  async getTask(id) {
    return this.request('GET', `/api/tasks/${id}`);
  }

  async confirmTask(id) {
    return this.request('POST', `/api/tasks/${id}/confirm`);
  }

  async cancelTask(id) {
    return this.request('POST', `/api/tasks/${id}/cancel`);
  }
}

const api = new ApiService();
export default api;
