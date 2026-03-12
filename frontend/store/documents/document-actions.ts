import { createAsyncThunk } from '@reduxjs/toolkit';
import { documentsApi, DocumentUpdateRequest } from '@/lib/api/documents';

// ── Fetch all documents ─────────────────────────────────────────────────────
export const fetchDocuments = createAsyncThunk(
  'documents/fetchDocuments',
  async (status: string | undefined, { rejectWithValue }) => {
    try {
      const response = await documentsApi.list(status);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Upload a document ───────────────────────────────────────────────────────
export const uploadDocument = createAsyncThunk(
  'documents/uploadDocument',
  async (
    { file, onProgress }: { file: File; onProgress?: (percent: number) => void },
    { rejectWithValue }
  ) => {
    try {
      const response = await documentsApi.upload(file, onProgress);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Delete a document ───────────────────────────────────────────────────────
export const deleteDocument = createAsyncThunk(
  'documents/deleteDocument',
  async (id: string, { rejectWithValue }) => {
    try {
      await documentsApi.delete(id);
      return id; // Return the ID so the slice can remove it from state
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);

// ── Update document metadata ────────────────────────────────────────────────
export const updateDocumentMetadata = createAsyncThunk(
  'documents/updateMetadata',
  async (
    { id, data }: { id: string; data: DocumentUpdateRequest },
    { rejectWithValue, dispatch }
  ) => {
    try {
      const response = await documentsApi.update(id, data);
      // Re-fetch documents to get the updated data
      dispatch(fetchDocuments(undefined));
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error);
    }
  }
);
