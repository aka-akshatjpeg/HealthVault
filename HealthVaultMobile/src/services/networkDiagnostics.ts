import { isAxiosError } from 'axios';
import { API_BASE_URL, API_URL_SOURCE, DEV_SERVER_HOST } from '@/constants';

/**
 * Network diagnostics.
 *
 * Privacy: nothing here ever reads or prints request/response headers, request
 * bodies (credentials, OTPs) or response bodies (patient data). Only the HTTP
 * method, the URL *path*, the status code and the axios error code are used.
 */

const originOf = (url: string) => {
  const m = url.match(/^https?:\/\/[^/]+/i);
  return m ? m[0] : url;
};

/** Log the resolved API configuration once (development only). */
export function logApiConfig() {
  if (!__DEV__) return;
  console.log(
    `[API] base=${API_BASE_URL || '(not configured)'} source=${API_URL_SOURCE} metro=${DEV_SERVER_HOST ?? 'n/a'}`
  );
  if (API_URL_SOURCE === 'unset') {
    console.warn('[API] EXPO_PUBLIC_API_URL is not set for this build.');
  }
  if (!/^https:/i.test(API_BASE_URL)) {
    console.warn('[API] Using a non-HTTPS API URL. Use HTTPS for production.');
  }
}

/** Log a failed request (development only, metadata only). */
export function logApiError(error: unknown) {
  if (!__DEV__ || !isAxiosError(error)) return;
  const method = (error.config?.method ?? '?').toUpperCase();
  const path = error.config?.url ?? '?'; // path relative to baseURL, no query secrets expected
  if (error.response) {
    console.log(`[API] ${method} ${path} -> HTTP ${error.response.status}`);
  } else {
    console.log(`[API] ${method} ${path} -> no response (${error.code ?? 'unknown'}) via ${originOf(API_BASE_URL)}`);
  }
}

/**
 * Turn an error from the API layer into a message safe to show the user.
 * - If the server answered with its own `error` message, that is preserved.
 * - If the server could not be reached, explain why (host only, no secrets).
 */
export function describeApiError(error: unknown, fallback: string): string {
  if (!API_BASE_URL) {
    return 'The app is not configured with a server address (EXPO_PUBLIC_API_URL).';
  }
  if (!isAxiosError(error)) return fallback;

  if (error.response) {
    const serverMsg = (error.response.data as { error?: unknown } | undefined)?.error;
    return typeof serverMsg === 'string' && serverMsg ? serverMsg : fallback;
  }

  const host = originOf(API_BASE_URL);
  const hint = __DEV__
    ? '\n\nCheck: Flask is running on 0.0.0.0:5000, the phone is on the same Wi-Fi as the PC, the PC firewall allows port 5000, and EXPO_PUBLIC_API_URL is correct.'
    : '';

  if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
    return `The server at ${host} took too long to respond.${hint}`;
  }
  return `Cannot reach the server at ${host}. Please check your connection.${hint}`;
}
