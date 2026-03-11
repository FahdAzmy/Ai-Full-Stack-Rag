import apiClient from './api-client';

// ── Types matching backend Pydantic schemas ─────────────────────────────────

export interface ChatListItem {
  id: string;
  title: string | null;
  created_at: string;
  message_count: number;
  last_message_at: string | null;
}

export interface SourceChunk {
  source_number: number;
  title: string | null;
  author: string | null;
  year: string | null;
  page_number: number | null;
  file_name: string | null;
  document_id: string | null;
  chunk_id: string | null;
  similarity: number | null;
  excerpt: string | null;
}

export interface MessageResponse {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source_chunks: SourceChunk[] | null;
  created_at: string;
}

export interface ChatDetailResponse {
  id: string;
  title: string | null;
  created_at: string;
  messages: MessageResponse[];
}

export interface QueryResponse {
  message_id: string;
  answer: string;
  sources: SourceChunk[];
}

// ── API Functions ───────────────────────────────────────────────────────────

export const chatsApi = {
  /** List all chats for the current user, newest first */
  list: () =>
    apiClient.get<ChatListItem[]>('/chats/'),

  /** Create a new chat session */
  create: (title?: string) =>
    apiClient.post('/chats/', { title: title || null }),

  /** Get a chat with all its messages */
  get: (id: string) =>
    apiClient.get<ChatDetailResponse>(`/chats/${id}`),

  /** Delete a chat and all its messages */
  delete: (id: string) =>
    apiClient.delete(`/chats/${id}`),

  /** Rename a chat */
  rename: (id: string, title: string) =>
    apiClient.patch(`/chats/${id}`, { title }),

  /** Send a research question and get a RAG-powered answer */
  query: (chatId: string, question: string, documentIds?: string[]) =>
    apiClient.post<QueryResponse>(`/chats/${chatId}/query`, {
      question,
      document_ids: documentIds || null,
    }),

  /** Get paginated message history */
  getMessages: (chatId: string, limit: number = 50, before?: string) => {
    const params: Record<string, any> = { limit };
    if (before) params.before = before;
    return apiClient.get<MessageResponse[]>(`/chats/${chatId}/messages`, { params });
  },
};
