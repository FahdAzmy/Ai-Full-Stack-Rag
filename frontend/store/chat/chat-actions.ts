import { createAsyncThunk } from '@reduxjs/toolkit';
import { chatsApi, ChatListItem } from '@/lib/api/chats';

// ── Fetch all chats ─────────────────────────────────────────────────────────
export const fetchChats = createAsyncThunk(
  'chat/fetchChats',
  async (_, { rejectWithValue }) => {
    try {
      const response = await chatsApi.list();
      const data = response.data;
      // Backend may return an array or an object like { chats: [...] }
      const chats: ChatListItem[] = Array.isArray(data)
        ? data
        : (data as any)?.chats ?? [];
      return chats;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Create a new chat ───────────────────────────────────────────────────────
export const createChat = createAsyncThunk(
  'chat/createChat',
  async (title: string | undefined, { rejectWithValue }) => {
    try {
      const response = await chatsApi.create(title);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Fetch a single chat with messages ───────────────────────────────────────
export const fetchChat = createAsyncThunk(
  'chat/fetchChat',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await chatsApi.get(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Delete a chat ───────────────────────────────────────────────────────────
export const deleteChat = createAsyncThunk(
  'chat/deleteChat',
  async (id: string, { rejectWithValue }) => {
    try {
      await chatsApi.delete(id);
      return id; // Return ID so slice can remove it
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Rename a chat ───────────────────────────────────────────────────────────
export const renameChat = createAsyncThunk(
  'chat/renameChat',
  async ({ id, title }: { id: string; title: string }, { rejectWithValue }) => {
    try {
      const response = await chatsApi.rename(id, title);
      return { id, title, data: response.data };
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

