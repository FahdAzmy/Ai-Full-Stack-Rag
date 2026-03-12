import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { ChatListItem, ChatDetailResponse, MessageResponse } from '@/lib/api/chats';
import {
  fetchChats,
  createChat,
  fetchChat,
  deleteChat,
  renameChat,
  sendQuery,
} from './chat-actions';

// ── State Interface ─────────────────────────────────────────────────────────

interface ChatState {
  chats: ChatListItem[];
  activeChat: ChatDetailResponse | null;
  loading: boolean;
  querying: boolean; // true while AI is generating a response
  error: string | null;
}

const initialState: ChatState = {
  chats: [],
  activeChat: null,
  loading: false,
  querying: false,
  error: null,
};

// ── Slice ───────────────────────────────────────────────────────────────────

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setActiveChat: (state, action: PayloadAction<ChatDetailResponse | null>) => {
      state.activeChat = action.payload;
    },
    appendMessage: (state, action: PayloadAction<MessageResponse>) => {
      if (state.activeChat) {
        state.activeChat.messages.push(action.payload);
      }
    },
    clearChatError: (state) => {
      state.error = null;
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

    // Send query
    builder
      .addCase(sendQuery.pending, (state, action) => {
        state.querying = true;
        state.error = null;
        // Optimistically add the user's message to the active chat
        if (state.activeChat) {
          state.activeChat.messages.push({
            id: `temp-${Date.now()}`,
            role: 'user',
            content: action.meta.arg.question,
            source_chunks: null,
            created_at: new Date().toISOString(),
          });
        }
      })
      .addCase(sendQuery.fulfilled, (state, action) => {
        state.querying = false;
        const { response } = action.payload;
        // Add the assistant's response
        if (state.activeChat) {
          state.activeChat.messages.push({
            id: response.message_id,
            role: 'assistant',
            content: response.answer,
            source_chunks: response.sources,
            created_at: new Date().toISOString(),
          });
        }
        // Update message count in the chat list
        const chatInList = state.chats.find((c) => c.id === action.payload.chatId);
        if (chatInList) {
          chatInList.message_count += 2; // user + assistant
          chatInList.last_message_at = new Date().toISOString();
        }
      })
      .addCase(sendQuery.rejected, (state, action) => {
        state.querying = false;
        state.error = action.payload as string;
      });
  },
});

export const { setActiveChat, appendMessage, clearChatError } = chatSlice.actions;
export default chatSlice.reducer;
