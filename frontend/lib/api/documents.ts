import apiClient from './api-client';

// ── Types matching backend Pydantic schemas ─────────────────────────────────

export interface DocumentListItem {
  id: string;
  file_name: string;
  title: string | null;
  author: string | null;
  year: string | null;
  status: 'uploading' | 'processing' | 'ready' | 'failed';
  total_pages: number | null;
  file_size: number | null;
  created_at: string;
}

export interface DocumentListResponse {
  documents: DocumentListItem[];
  total: number;
}

export interface DocumentDetail extends DocumentListItem {
  journal: string | null;
  doi: string | null;
  abstract: string | null;
  error_message: string | null;
  updated_at: string | null;
  chunk_count: number;
}

export interface DocumentUploadResponse {
  id: string;
  file_name: string;
  file_size: number;
  status: string;
  message: string;
}

export interface DocumentUpdateRequest {
  title?: string;
  author?: string;
  year?: string;
  journal?: string;
  doi?: string;
}

export interface DocumentUpdateResponse {
  message: string;
  id: string;
}

// ── API Functions ───────────────────────────────────────────────────────────

export const documentsApi = {
  /** List all documents, optionally filtered by status */
  list: (status?: string) => {
    const params = status ? { status } : {};
    return apiClient.get<DocumentListResponse>('/documents/', { params });
  },

  /** Upload a PDF file with optional progress callback */
  upload: (file: File, onProgress?: (percent: number) => void) => {
    const formData = new FormData();
    formData.append('file', file);

    return apiClient.post<DocumentUploadResponse>('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded * 100) / e.total));
        }
      },
    });
  },

  /** Get detailed info for a single document */
  get: (id: string) =>
    apiClient.get<DocumentDetail>(`/documents/${id}`),

  /** Update document metadata (all fields optional) */
  update: (id: string, data: DocumentUpdateRequest) =>
    apiClient.patch<DocumentUpdateResponse>(`/documents/${id}`, data),

  /** Delete a document and all associated data */
  delete: (id: string) =>
    apiClient.delete(`/documents/${id}`),
};
