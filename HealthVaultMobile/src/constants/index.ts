import { Platform } from 'react-native';
import Constants from 'expo-constants';

export { Colors } from './colors';

/**
 * Backend (Flask) base URL.
 *
 * Resolution order:
 *   1. EXPO_PUBLIC_API_URL (set in .env.local for development, or in EAS /
 *      build environment for production, e.g. https://api.example.com).
 *   2. Development-only default that works for an emulator/simulator running
 *      on the same machine as Flask:
 *        - Android emulator -> http://10.0.2.2:5000 (alias for the host PC)
 *        - iOS simulator    -> http://localhost:5000
 *   3. Nothing (production without EXPO_PUBLIC_API_URL) -> requests fail with a
 *      clear configuration error instead of silently hitting a wrong host.
 *
 * NOTE: the Expo dev-server host (Constants.expoConfig.hostUri) is the *Metro*
 * machine/port and is NOT assumed to be the Flask backend. It is only exposed
 * below for diagnostics.
 *
 * A physical iPhone/Android device cannot use localhost/10.0.2.2, so it MUST
 * have EXPO_PUBLIC_API_URL set to the PC's LAN address (http://<LAN-IP>:5000).
 */
const configuredUrl = process.env.EXPO_PUBLIC_API_URL?.trim();

const devDefaultUrl = Platform.OS === 'android' ? 'http://10.0.2.2:5000' : 'http://localhost:5000';

export const API_BASE_URL = (configuredUrl || (__DEV__ ? devDefaultUrl : '')).replace(/\/+$/, '');
export const API_URL_SOURCE: 'env' | 'dev-default' | 'unset' = configuredUrl
  ? 'env'
  : __DEV__
    ? 'dev-default'
    : 'unset';
export const API_V1 = `${API_BASE_URL}/api/v1`;

/** Metro/Expo dev-server host:port (diagnostics only; undefined in release builds). */
export const DEV_SERVER_HOST: string | undefined = Constants.expoConfig?.hostUri;
