import { configureStore } from '@reduxjs/toolkit';
import authReducer from '@/store/auth/auth-slice';
import documentReducer from '@/store/documents/document-slice';
import chatReducer from '@/store/chat/chat-slice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    documents: documentReducer,
    chat: chatReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
