'use client';

import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '@/store/store';
import { fetchChats } from '@/store/chat/chat-actions';
import { fetchDocuments } from '@/store/documents/document-actions';
import { ChatLayout } from '@/components/chat/chat-layout';

export default function ChatPage() {
  const dispatch = useDispatch<AppDispatch>();

  // Fetch chats and documents when the page loads
  useEffect(() => {
    dispatch(fetchChats());
    dispatch(fetchDocuments(undefined));
  }, [dispatch]);

  return <ChatLayout />;
}
