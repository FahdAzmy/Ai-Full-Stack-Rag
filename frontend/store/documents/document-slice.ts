import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { DocumentListItem } from '@/lib/api/documents';
import {
  fetchDocuments,
  uploadDocument,
  deleteDocument,
  updateDocumentMetadata,
} from './document-actions';

// ── State Interface ─────────────────────────────────────────────────────────

interface DocumentState {
  documents: DocumentListItem[];
  total: number;
  loading: boolean;
  uploading: boolean;
  uploadProgress: number;
  error: string | null;
  selectedDocumentIds: string[]; // For chat filtering
}

const initialState: DocumentState = {
  documents: [],
  total: 0,
  loading: false,
  uploading: false,
  uploadProgress: 0,
  error: null,
  selectedDocumentIds: [],
};

// ── Slice ───────────────────────────────────────────────────────────────────

const documentSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    toggleDocumentSelection: (state, action: PayloadAction<string>) => {
      const id = action.payload;
      const idx = state.selectedDocumentIds.indexOf(id);
      if (idx >= 0) {
        state.selectedDocumentIds.splice(idx, 1);
      } else {
        state.selectedDocumentIds.push(id);
      }
    },
    clearSelection: (state) => {
      state.selectedDocumentIds = [];
    },
    clearDocumentError: (state) => {
      state.error = null;
    },
    setUploadProgress: (state, action: PayloadAction<number>) => {
      state.uploadProgress = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch documents
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.loading = false;
        state.documents = action.payload.documents;
        state.total = action.payload.total;
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Upload document
    builder
      .addCase(uploadDocument.pending, (state) => {
        state.uploading = true;
        state.uploadProgress = 0;
        state.error = null;
      })
      .addCase(uploadDocument.fulfilled, (state) => {
        state.uploading = false;
        state.uploadProgress = 100;
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.uploading = false;
        state.uploadProgress = 0;
        state.error = action.payload as string;
      });

    // Delete document
    builder
      .addCase(deleteDocument.fulfilled, (state, action) => {
        const deletedId = action.payload;
        state.documents = state.documents.filter((d) => d.id !== deletedId);
        state.total = Math.max(0, state.total - 1);
        // Also remove from selection if selected
        state.selectedDocumentIds = state.selectedDocumentIds.filter((id) => id !== deletedId);
      })
      .addCase(deleteDocument.rejected, (state, action) => {
        state.error = action.payload as string;
      });

    // Update metadata
    builder
      .addCase(updateDocumentMetadata.rejected, (state, action) => {
        state.error = action.payload as string;
      });
  },
});

export const {
  toggleDocumentSelection,
  clearSelection,
  clearDocumentError,
  setUploadProgress,
} = documentSlice.actions;

export default documentSlice.reducer;
