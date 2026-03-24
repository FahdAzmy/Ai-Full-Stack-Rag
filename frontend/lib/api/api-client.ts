import axios from 'axios';
import { attachAuthInterceptors } from '@/lib/token-refresh';

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

// Attach the shared auth + refresh interceptors
attachAuthInterceptors(apiClient);

export default apiClient;
