/**
 * FarmSync Centralized REST API Client (Step 14)
 * Handles JWT token storage, authorization headers, automatic token refresh,
 * standardized response unpacking, and error handling.
 */

const API_BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? `${window.location.origin}/api/v1`
  : '/api/v1';

class ApiClient {
  constructor() {
    this.accessTokenKey = 'farmsync_access_token';
    this.refreshTokenKey = 'farmsync_refresh_token';
    this.userKey = 'farmsync_user';
  }

  getAccessToken() {
    return localStorage.getItem(this.accessTokenKey);
  }

  getRefreshToken() {
    return localStorage.getItem(this.refreshTokenKey);
  }

  getUser() {
    try {
      const userStr = localStorage.getItem(this.userKey);
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      return null;
    }
  }

  isAuthenticated() {
    return !!this.getAccessToken();
  }

  isStaffOrAdmin() {
    const user = this.getUser();
    return user ? (user.is_staff || user.is_superuser || user.role === 'admin') : false;
  }

  setSession(access, refresh, user) {
    if (access) localStorage.setItem(this.accessTokenKey, access);
    if (refresh) localStorage.setItem(this.refreshTokenKey, refresh);
    if (user) localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  clearSession() {
    localStorage.removeItem(this.accessTokenKey);
    localStorage.removeItem(this.refreshTokenKey);
    localStorage.removeItem(this.userKey);
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    const headers = options.headers || {};

    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = headers['Content-Type'] || 'application/json';
    }

    const token = this.getAccessToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers
    };

    let response;
    try {
      response = await fetch(url, config);
    } catch (networkError) {
      throw new Error(`Network error: Unable to connect to server (${networkError.message})`);
    }

    // Handle 401 Token Expiration with Automatic Refresh Retry
    if (response.status === 401 && this.getRefreshToken() && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this.getAccessToken()}`;
        return this.request(endpoint, options);
      } else {
        this.clearSession();
        window.dispatchEvent(new CustomEvent('farmsync:unauthorized'));
        throw new Error("Session expired. Please log in again.");
      }
    }

    let payload = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      try {
        payload = await response.json();
      } catch (e) {
        payload = null;
      }
    }

    if (!response.ok) {
      const errorMsg = payload?.message || payload?.detail || payload?.error || `Request failed with status ${response.status}`;
      const error = new Error(errorMsg);
      error.status = response.status;
      error.payload = payload;
      throw error;
    }

    return payload;
  }

  async refreshToken() {
    const refresh = this.getRefreshToken();
    if (!refresh) return false;

    try {
      const res = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh })
      });

      if (res.ok) {
        const data = await res.json();
        const newAccess = data.data?.access || data.access;
        if (newAccess) {
          localStorage.setItem(this.accessTokenKey, newAccess);
          return true;
        }
      }
    } catch (e) {
      // Refresh failed
    }
    return false;
  }

  // ==========================================
  // AUTHENTICATION APIs
  // ==========================================
  async login(username, password) {
    const res = await this.request('/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    if (res.data) {
      this.setSession(res.data.access, res.data.refresh, res.data.user);
    }
    return res.data;
  }

  async getMe() {
    const res = await this.request('/auth/me/');
    if (res.data) {
      localStorage.setItem(this.userKey, JSON.stringify(res.data));
    }
    return res.data;
  }

  async logout() {
    const refresh = this.getRefreshToken();
    try {
      if (refresh) {
        await this.request('/auth/logout/', {
          method: 'POST',
          body: JSON.stringify({ refresh })
        });
      }
    } catch (e) {
      // Ignore logout errors
    } finally {
      this.clearSession();
      window.dispatchEvent(new CustomEvent('farmsync:unauthorized'));
    }
  }

  // ==========================================
  // DASHBOARD APIs
  // ==========================================
  async getDashboardSummary() {
    const res = await this.request('/dashboard/summary/');
    return res.data;
  }

  async getDashboardActivity() {
    const res = await this.request('/dashboard/recent-activity/');
    return res.data;
  }

  // ==========================================
  // FARMERS APIs
  // ==========================================
  async getFarmers(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await this.request(`/farmers/${query ? `?${query}` : ''}`);
    return res.data;
  }

  async getFarmer(id) {
    const res = await this.request(`/farmers/${id}/`);
    return res.data;
  }

  async createFarmer(farmerData) {
    const res = await this.request('/farmers/', {
      method: 'POST',
      body: JSON.stringify(farmerData)
    });
    return res.data;
  }

  async updateFarmer(id, farmerData) {
    const res = await this.request(`/farmers/${id}/`, {
      method: 'PUT',
      body: JSON.stringify(farmerData)
    });
    return res.data;
  }

  async deleteFarmer(id) {
    const res = await this.request(`/farmers/${id}/`, {
      method: 'DELETE'
    });
    return res;
  }

  // ==========================================
  // ATTENDANCE APIs
  // ==========================================
  async getAttendance(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await this.request(`/attendance/${query ? `?${query}` : ''}`);
    return res.data;
  }

  async checkIn(farmerId, location = null) {
    const body = { farmer_id: farmerId };
    if (location) body.device_location = location;
    const res = await this.request('/attendance/check-in/', {
      method: 'POST',
      body: JSON.stringify(body)
    });
    return res.data;
  }

  async checkOut(farmerId, location = null) {
    const body = { farmer_id: farmerId };
    if (location) body.device_location = location;
    const res = await this.request('/attendance/check-out/', {
      method: 'POST',
      body: JSON.stringify(body)
    });
    return res.data;
  }

  async getAttendanceReport(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await this.request(`/attendance/report/${query ? `?${query}` : ''}`);
    return res.data;
  }

  // ==========================================
  // TASKS APIs
  // ==========================================
  async getTasks(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await this.request(`/tasks/${query ? `?${query}` : ''}`);
    return res.data;
  }

  async createTask(taskData) {
    const res = await this.request('/tasks/', {
      method: 'POST',
      body: JSON.stringify(taskData)
    });
    return res.data;
  }

  async updateTask(id, taskData) {
    const res = await this.request(`/tasks/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(taskData)
    });
    return res.data;
  }

  async deleteTask(id) {
    const res = await this.request(`/tasks/${id}/`, {
      method: 'DELETE'
    });
    return res;
  }

  // ==========================================
  // DETECTION & CAMERA APIs
  // ==========================================
  async getDetectionStatus() {
    const res = await this.request('/detection/status/');
    return res.data;
  }

  async toggleDetection(enabled) {
    const res = await this.request('/detection/status/', {
      method: 'PATCH',
      body: JSON.stringify({ detection_enabled: enabled })
    });
    return res.data;
  }

  async analyzeImage(file, fieldName = 'Main Field') {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('field', fieldName);

    const res = await this.request('/detection/analyze/', {
      method: 'POST',
      body: formData
    });
    return res.data;
  }

  async getDetectionLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await this.request(`/detection/logs/${query ? `?${query}` : ''}`);
    return res.data;
  }

  getStreamUrl() {
    const token = this.getAccessToken();
    return token
      ? `${API_BASE_URL}/detection/stream/?token=${encodeURIComponent(token)}`
      : `${API_BASE_URL}/detection/stream/`;
  }

  // ==========================================
  // ALERTS APIs (READ-ONLY)
  // ==========================================
  async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await this.request(`/alerts/${query ? `?${query}` : ''}`);
    return res.data;
  }

  async getAlertDetail(id) {
    const res = await this.request(`/alerts/${id}/`);
    return res.data;
  }

  // ==========================================
  // SETTINGS APIs
  // ==========================================
  async getSettings() {
    const res = await this.request('/settings/');
    return res.data;
  }

  async updateSettings(settingsData) {
    const res = await this.request('/settings/', {
      method: 'PATCH',
      body: JSON.stringify(settingsData)
    });
    return res.data;
  }

  async getEmailSender() {
    const res = await this.request('/settings/email-sender/');
    return res.data;
  }

  async updateEmailSender(senderData) {
    const res = await this.request('/settings/email-sender/', {
      method: 'PUT',
      body: JSON.stringify(senderData)
    });
    return res.data;
  }

  async getReceivers() {
    const res = await this.request('/settings/receivers/');
    return res.data;
  }

  async createReceiver(receiverData) {
    const res = await this.request('/settings/receivers/', {
      method: 'POST',
      body: JSON.stringify(receiverData)
    });
    return res.data;
  }

  async deleteReceiver(id) {
    const res = await this.request(`/settings/receivers/${id}/`, {
      method: 'DELETE'
    });
    return res;
  }
}

// Global API singleton instance
window.api = new ApiClient();
