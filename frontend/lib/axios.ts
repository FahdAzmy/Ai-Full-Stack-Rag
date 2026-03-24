import axios from 'axios';
import { attachAuthInterceptors } from '@/lib/token-refresh';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// In-memory access token storage (never persisted to disk)
let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

const axiosInstance = axios.create({
  baseURL: `${API_URL}/auth`,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Attach the shared auth + refresh interceptors
attachAuthInterceptors(axiosInstance);

export default axiosInstance;
