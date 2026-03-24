import axios, { AxiosInstance } from 'axios';
import { getAccessToken, setAccessToken } from '@/lib/axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Shared refresh state (singleton across all axios instances) ──────────────

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// ── Attach interceptors to any axios instance ───────────────────────────────

export function attachAuthInterceptors(instance: AxiosInstance) {
  // Request interceptor — attach Bearer token
  instance.interceptors.request.use(
    (config) => {
      const token = getAccessToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error),
  );

  // Response interceptor — handle 401 + token refresh + error normalisation
  instance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      // Token Refresh Logic
      if (
        error.response?.status === 401 &&
        !originalRequest._retry &&
        !originalRequest.url?.endsWith('/refresh') &&
        !originalRequest.url?.endsWith('/login')
      ) {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              originalRequest.headers['Authorization'] = 'Bearer ' + token;
              return instance(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          // Use a bare axios call to avoid interceptor loops
          const response = await axios.post(
            `${API_URL}/auth/refresh`,
            {},
            { withCredentials: true },
          );

          const newToken = response.data.access_token;
          setAccessToken(newToken);
          processQueue(null, newToken);

          originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          return instance(originalRequest);
        } catch (refreshError) {
          processQueue(refreshError, null);
          setAccessToken(null);
          if (typeof window !== 'undefined') {
            window.location.href = '/auth';
          }
          return Promise.reject(refreshError);
        } finally {
          isRefreshing = false;
        }
      }

      // ── Normalise error message ────────────────────────────────────────
      let message = 'An error occurred';

      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;
        if (Array.isArray(detail)) {
          message = detail
            .map((err: { msg?: string }) => {
              const msg = err.msg || 'Invalid input';
              if (msg.includes('String should have at least')) {
                return 'passwordTooShort';
              }
              return msg;
            })
            .join(', ');
        } else if (typeof detail === 'string') {
          message = detail;
        } else if (typeof detail === 'object' && detail.code) {
          message = detail.code;
        }
      } else if (error.message) {
        message = error.message;
      }

      return Promise.reject(message);
    },
  );
}
