import axios from 'axios';
import * as SecureStore from 'expo-secure-store';
import { API_V1 } from '@/constants';
import { logApiConfig, logApiError } from './networkDiagnostics';

export const api = axios.create({
  baseURL: API_V1,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

logApiConfig();

// Attach JWT token to every request
api.interceptors.request.use(async (config) => {
  const token = await SecureStore.getItemAsync('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refreshToken = await SecureStore.getItemAsync('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
        const res = await axios.post(`${API_V1}/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${refreshToken}` },
        });
        const newToken = res.data.access_token;
        await SecureStore.setItemAsync('access_token', newToken);
        original.headers.Authorization = `Bearer ${newToken}`;
        return api(original);
      } catch {
        await SecureStore.deleteItemAsync('access_token');
        await SecureStore.deleteItemAsync('refresh_token');
        // Navigation to login handled by auth store
      }
    }
    return Promise.reject(error);
  }
);

// Dev-only diagnostics (method, path, status/code only; never headers or bodies)
api.interceptors.response.use(undefined, (error) => {
  logApiError(error);
  return Promise.reject(error);
});
