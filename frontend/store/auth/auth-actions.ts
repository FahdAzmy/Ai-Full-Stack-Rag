import { createAsyncThunk } from '@reduxjs/toolkit';
import axiosInstance, { setAccessToken } from '@/lib/axios';

// Login Action
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/login', credentials);
      // Save access token in memory only
      setAccessToken(response.data.access_token);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Signup Action
export const signup = createAsyncThunk(
  'auth/signup',
  async (userData: { name: string; email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/signup', userData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Verify Email Action
export const verifyEmail = createAsyncThunk(
  'auth/verify',
  async (verifyData: { email: string; code: string }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/verify-code', verifyData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Resend Code Action
export const resendCode = createAsyncThunk(
  'auth/resend',
  async (email: string, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/resend-code', { email });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Forgot Password Action
export const forgotPassword = createAsyncThunk(
  'auth/forgotPassword',
  async (email: string, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/forgot-password', { email });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Reset Password Action
export const resetPassword = createAsyncThunk(
  'auth/resetPassword',
  async (data: { email: string; code: string; new_password: string }, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.post('/reset-password', data);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Logout Action
export const logout = createAsyncThunk(
  'auth/logout',
  async (_, { rejectWithValue }) => {
    try {
      await axiosInstance.post('/logout');
      // Clear access token from memory
      setAccessToken(null);
      return null;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// Refresh Token Action — calls /refresh, saves access token in memory, then fetches profile
export const refreshToken = createAsyncThunk(
  'auth/refresh',
  async (_, { rejectWithValue }) => {
    try {
      // Step 1: Call refresh endpoint (sends refresh_token cookie automatically)
      const refreshResponse = await axiosInstance.post('/refresh');
      const newAccessToken = refreshResponse.data.access_token;

      // Step 2: Save access token in memory
      setAccessToken(newAccessToken);

      // Step 3: Call profile endpoint with the new access token
      const profileResponse = await axiosInstance.get('/profile');

      // Return both the access token and user data
      return {
        access_token: newAccessToken,
        user: profileResponse.data,
      };
    } catch (error: any) {
      // Clear token on failure
      setAccessToken(null);
      return rejectWithValue(error);
    }
  }
);

// Get Profile Action
export const getProfile = createAsyncThunk(
  'auth/getProfile',
  async (_, { rejectWithValue }) => {
    try {
      const response = await axiosInstance.get('/profile');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);
