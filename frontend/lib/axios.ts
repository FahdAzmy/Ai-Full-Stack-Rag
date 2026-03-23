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

let isRefreshing = false;
let failedQueue: Array<{ resolve: (value?: unknown) => void, reject: (reason?: any) => void }> = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor for error handling and silent token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Token Refresh Logic: If 401 Unauthorized and it's not the refresh or login endpoint itself
    if (
      error.response?.status === 401 && 
      !originalRequest._retry && 
      originalRequest.url !== '/refresh' && 
      originalRequest.url !== '/login'
    ) {
      if (isRefreshing) {
        // If already refreshing, put the request in a queue
        return new Promise(function(resolve, reject) {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = 'Bearer ' + token;
          return axiosInstance(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        // Send refresh request using naked axios to avoid interceptor loop
        const response = await axios.post(`${API_URL}/auth/refresh`, {}, {
          withCredentials: true,
        });

        const newToken = response.data.access_token;
        setAccessToken(newToken);
        processQueue(null, newToken);

        // Update the failed request's header and retry it!
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
        return axiosInstance(originalRequest);
      } catch (refreshError) {
        // If refresh fails (e.g., refresh token expired), clear state and logout
        processQueue(refreshError, null);
        setAccessToken(null);
        if (typeof window !== 'undefined') {
          // Force user back to login
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Default error mapping logic (runs if it's not a 401, or if refresh failed)
    let message = 'An error occurred';
    
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (Array.isArray(detail)) {
        // Handle Pydantic validation errors
        message = detail.map((err: any) => {
            const msg = err.msg || 'Invalid input';
            if (msg.includes('String should have at least')) {
                return 'passwordTooShort'; 
            }
            return msg;
        }).join(', ');
      } else if (typeof detail === 'string') {
        message = detail;
      } else if (typeof detail === 'object') {
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
