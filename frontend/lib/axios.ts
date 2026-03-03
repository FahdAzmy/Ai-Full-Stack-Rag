import axios, { AxiosRequestConfig } from 'axios';

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
  withCredentials: true, // For cookie support
});

// Request interceptor to add token from memory
axiosInstance.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'An error occurred';
    
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        // Handle Pydantic validation errors (array of objects)
        message = detail.map((err: any) => {
            const msg = err.msg || 'Invalid input';
            if (msg.includes('String should have at least')) {
                return 'passwordTooShort'; 
            }
            // Add more specific mappings here if needed
            return msg;
        }).join(', ');
      } else if (typeof detail === 'string') {
        message = detail;
      } else if (typeof detail === 'object') {
          // Check for structured error from backend (AppException)
          if (detail.code) {
             message = detail.code;
          } else {
             message = JSON.stringify(detail);
          }
      }
    } else if (error.message) {
      message = error.message;
    }
    
    return Promise.reject(message);
  }
);

export default axiosInstance;
