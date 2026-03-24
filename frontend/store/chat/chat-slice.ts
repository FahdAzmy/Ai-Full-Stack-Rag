import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatListItem, ChatDetailResponse, MessageResponse } from '@/lib/api/chats';
import {
  fetchChats,
  createChat,
  fetchChat,
  deleteChat,
  renameChat,
} from './chat-actions';

// ── State Interface ─────────────────────────────────────────────────────────

interface ChatState {
  chats: ChatListItem[];
  activeChat: ChatDetailResponse | null;
  loading: boolean;
  querying: boolean; // true while AI is generating a response
  error: string | null;
  sidebarOpen: boolean;
}

const initialState: ChatState = {
  chats: [],
  activeChat: null,
  loading: false,
  querying: false,
  error: null,
  sidebarOpen: false,
};

// ── Slice ───────────────────────────────────────────────────────────────────

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setActiveChat: (state, action: PayloadAction<ChatDetailResponse | null>) => {
      state.activeChat = action.payload;
    },
    appendUserMessage: (state, action: PayloadAction<MessageResponse>) => {
      if (state.activeChat) {
        state.activeChat.messages.push(action.payload);
      }
    },
    startStreamingMessage: (state, action: PayloadAction<{ sources: any[] | null }>) => {
      if (state.activeChat) {
        state.activeChat.messages.push({
          id: 'streaming',
          role: 'assistant',
          content: '',
          source_chunks: action.payload.sources,
          created_at: new Date().toISOString(),
        });
      }
      state.querying = true;
    },
    appendTokenToStreamingMessage: (state, action: PayloadAction<string>) => {
      if (state.activeChat) {
        const lastMsg = state.activeChat.messages[state.activeChat.messages.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.id === 'streaming') {
          lastMsg.content += action.payload;
        }
      }
    },
    finalizeStreamingMessage: (state, action: PayloadAction<{ id: string; sources: any[] | null; title?: string | null }>) => {
      if (state.activeChat) {
        const lastMsg = state.activeChat.messages[state.activeChat.messages.length - 1];
        if (lastMsg && lastMsg.role === 'assistant' && lastMsg.id === 'streaming') {
          lastMsg.id = action.payload.id;
          lastMsg.source_chunks = action.payload.sources;
        }
        
        // Update Title dynamically if provided from the backend
        if (action.payload.title && state.activeChat.title !== action.payload.title) {
          state.activeChat.title = action.payload.title;
          const chatInList = state.chats.find(c => c.id === state.activeChat!.id);
          if (chatInList) {
            chatInList.title = action.payload.title;
          }
        }
      }
      state.querying = false;
    },
    setQuerying: (state, action: PayloadAction<boolean>) => {
      state.querying = action.payload;
    },
    setChatError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
    },
    clearChatError: (state) => {
      state.error = null;
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
  },
  extraReducers: (builder) => {
    // Fetch chats list
    builder
      .addCase(fetchChats.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchChats.fulfilled, (state, action) => {
        state.loading = false;
        state.chats = action.payload;
      })
      .addCase(fetchChats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Create chat
    builder
      .addCase(createChat.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createChat.fulfilled, (state, action) => {
        state.loading = false;
        // Add the new chat to the front of the list
        const newChat = action.payload;
        state.chats.unshift({
          id: newChat.id,
          title: newChat.title || null,
          created_at: newChat.created_at || new Date().toISOString(),
          message_count: 0,
          last_message_at: null,
        });
        // Set it as active with empty messages
        state.activeChat = {
          id: newChat.id,
          title: newChat.title || null,
          created_at: newChat.created_at || new Date().toISOString(),
          messages: [],
        };
      })
      .addCase(createChat.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch single chat (with messages)
    builder
      .addCase(fetchChat.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchChat.fulfilled, (state, action) => {
        state.loading = false;
        state.activeChat = action.payload;
      })
      .addCase(fetchChat.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Delete chat
    builder
      .addCase(deleteChat.fulfilled, (state, action) => {
        const deletedId = action.payload;
        state.chats = state.chats.filter((c) => c.id !== deletedId);
        // Clear active chat if it was deleted
        if (state.activeChat?.id === deletedId) {
          state.activeChat = null;
        }
      })
      .addCase(deleteChat.rejected, (state, action) => {
        state.error = action.payload as string;
      });

    // Rename chat
    builder
      .addCase(renameChat.fulfilled, (state, action) => {
        const { id, title } = action.payload;
        // Update in the chat list
        const chat = state.chats.find((c) => c.id === id);
        if (chat) chat.title = title;
        // Update active chat if it's the same
        if (state.activeChat?.id === id) {
          state.activeChat.title = title;
        }
      })
      .addCase(renameChat.rejected, (state, action) => {
        state.error = action.payload as string;
      });


  },
});

export const {
  setActiveChat,
  appendUserMessage,
  startStreamingMessage,
  appendTokenToStreamingMessage,
  finalizeStreamingMessage,
  setQuerying,
  setChatError,
  clearChatError,
  setSidebarOpen,
} = chatSlice.actions;

export default chatSlice.reducer;
