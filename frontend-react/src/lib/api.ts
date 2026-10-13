// API Client for the Incident War Room

const API_BASE = 'http://127.0.0.1:8000/api/v1';

export const WS_BASE = (import.meta as any).env?.VITE_WS_BASE || 'ws://127.0.0.1:8000';

export const api = {
  getToken: () => localStorage.getItem('token'),
  
  setToken: (token: string) => {
    localStorage.setItem('token', token);
  },
  
  logout: () => {
    localStorage.removeItem('token');
  },

  getWebSocketUrl: (incidentId: string) => {
    const token = localStorage.getItem('token') || '';
    return `${WS_BASE}/ws/incidents/${incidentId}?token=${token}`;
  },

  async request(endpoint: string, options: RequestInit = {}) {
    const token = this.getToken();
    const headers = new Headers(options.headers || {});
    
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    if (!(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.logout();
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'An error occurred');
    }

    return response.json();
  },

  // Auth
  login: (data: any) => api.request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data: any) => api.request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getDepartments: () => api.request('/auth/departments'),
  getMe: () => api.request('/auth/me'),
  getUsers: () => api.request('/auth/users'),

  // Incidents
  getIncidents: () => api.request('/incidents'),
  getIncident: (id: string) => api.request(`/incidents/${id}`),
  createIncident: (data: any) => api.request('/incidents', { method: 'POST', body: JSON.stringify(data) }),
  updateStatus: (id: string, data: any) => api.request(`/incidents/${id}/status`, { method: 'PATCH', body: JSON.stringify(data) }),
  updateSeverity: (id: string, data: any) => api.request(`/incidents/${id}/severity`, { method: 'PATCH', body: JSON.stringify(data) }),
  resolveIncident: (id: string, data: any) => api.request(`/incidents/${id}/resolve`, { method: 'POST', body: JSON.stringify(data) }),

  // Participants
  getParticipants: (id: string) => api.request(`/incidents/${id}/participants`),
  addParticipant: (id: string, data: any) => api.request(`/incidents/${id}/participants`, { method: 'POST', body: JSON.stringify(data) }),

  // Messages
  getMessages: (id: string) => api.request(`/incidents/${id}/messages`),
  postMessage: (id: string, data: any) => api.request(`/incidents/${id}/messages`, { method: 'POST', body: JSON.stringify(data) }),

  // Events
  getEvents: (id: string) => api.request(`/incidents/${id}/events`),
};

