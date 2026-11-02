import { api } from './api';
import * as SecureStore from 'expo-secure-store';
import { getAuth, signOut } from '@react-native-firebase/auth';

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
  /**
   * Exchange a Firebase ID token for a HealthVault JWT pair.
   * Called after every successful Firebase sign-in (phone, Google, Apple).
   */
  async firebaseLogin(idToken: string, profile?: { full_name?: string }): Promise<TokenResponse> {
    const res = await api.post('/auth/firebase-login', { id_token: idToken, ...(profile || {}) });
    const data: TokenResponse = res.data;
    await SecureStore.setItemAsync('access_token', data.access_token);
    await SecureStore.setItemAsync('refresh_token', data.refresh_token);
    await SecureStore.setItemAsync('user', JSON.stringify(data.user));
    return data;
  },

  /** Link a verified Firebase phone identity to an existing account. */
  async linkExistingAccount(idToken: string, email: string, password: string): Promise<TokenResponse> {
    const res = await api.post('/auth/firebase-link', { id_token: idToken, email, password });
    const data: TokenResponse = res.data;
    await SecureStore.setItemAsync('access_token', data.access_token);
    await SecureStore.setItemAsync('refresh_token', data.refresh_token);
    await SecureStore.setItemAsync('user', JSON.stringify(data.user));
    return data;
  },

  async logout() {
    try { await signOut(getAuth()); } catch { /* No Firebase user may be signed in. */ }
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
