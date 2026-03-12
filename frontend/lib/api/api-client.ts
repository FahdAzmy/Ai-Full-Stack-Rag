import axios from 'axios';
import { getAccessToken } from '@/lib/axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * General-purpose axios instance for non-auth API calls.
 * Unlike the auth-specific instance in lib/axios.ts (baseURL: /auth),
 * this one uses the root API URL so it can reach /documents/, /chats/, etc.
 */
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Attach Bearer token from in-memory storage
apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Normalize error responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An error occurred';

    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        message = detail.map((err: any) => err.msg || 'Invalid input').join(', ');
      } else if (typeof detail === 'string') {
        message = detail;
      } else if (typeof detail === 'object' && detail.code) {
        message = detail.code;
      }
    } else if (error.message) {
      message = error.message;
    }

    return Promise.reject(message);
  }
);

export default apiClient;
