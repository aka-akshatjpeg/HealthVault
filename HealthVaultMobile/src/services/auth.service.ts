import { api } from './api';
import * as SecureStore from 'expo-secure-store';

export interface LoginResponse {
  otp_pending: boolean;
  user_id: string;
  otp_code: string;
  role: string;
  message: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  role: string;
  user: {
    id: string;
    email: string;
    role: string;
    full_name?: string;
    hv_id?: string;
  };
}

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const res = await api.post('/auth/login', { email, password });
    return res.data;
  },

  async verifyOtp(userId: string, otp: string): Promise<TokenResponse> {
    const res = await api.post('/auth/verify-otp', { user_id: userId, otp });
    const data: TokenResponse = res.data;
    await SecureStore.setItemAsync('access_token', data.access_token);
    await SecureStore.setItemAsync('refresh_token', data.refresh_token);
    await SecureStore.setItemAsync('user', JSON.stringify(data.user));
    return data;
  },

  async register(payload: Record<string, string>): Promise<TokenResponse> {
    const res = await api.post('/auth/register', payload);
    const data: TokenResponse = res.data;
    await SecureStore.setItemAsync('access_token', data.access_token);
    await SecureStore.setItemAsync('refresh_token', data.refresh_token);
    await SecureStore.setItemAsync('user', JSON.stringify(data.user));
    return data;
  },

  async logout() {
    await SecureStore.deleteItemAsync('access_token');
    await SecureStore.deleteItemAsync('refresh_token');
    await SecureStore.deleteItemAsync('user');
  },

  async getStoredUser() {
    const raw = await SecureStore.getItemAsync('user');
    if (!raw) return null;
    try { return JSON.parse(raw); } catch { return null; }
  },
};
