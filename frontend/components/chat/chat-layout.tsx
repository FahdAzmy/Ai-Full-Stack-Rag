'use client';

import { useRef, useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { RootState, AppDispatch } from '@/store/store';
import { setSidebarOpen } from '@/store/chat/chat-slice';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { DocumentSidebar } from '@/components/documents/document-sidebar';
import { useLanguage } from '@/lib/language-context';

export function ChatLayout() {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { activeChat, querying, loading, sidebarOpen } = useSelector((state: RootState) => state.chat);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [docSidebarOpen, setDocSidebarOpen] = useState(true);

  // Auto-scroll to bottom when messages change or when querying starts/stops
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeChat?.messages, querying]);

  const chatTitle = activeChat?.title || t('chatUntitled') || 'New Chat';

  return (
    <div className="flex h-full w-full bg-white dark:bg-background-dark overflow-hidden font-display relative">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col relative bg-white dark:bg-background-dark min-w-0">
        {/* Header */}
        <header className="h-16 border-b border-border-cream dark:border-gray-800 flex items-center justify-between px-8 bg-white/80 dark:bg-background-dark/80 backdrop-blur-md sticky top-0 z-10 transition-colors shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <button 
              onClick={() => dispatch(setSidebarOpen(!sidebarOpen))}
              className="p-1 -ml-2 text-primary/60 dark:text-emerald-500/60 hover:text-primary dark:hover:text-emerald-400 transition-colors rounded-md"
            >
              <span className="material-symbols-outlined">{sidebarOpen ? 'menu_open' : 'menu'}</span>
            </button>
            <h2 className="text-sm font-semibold text-primary dark:text-emerald-400 truncate">
              {activeChat ? chatTitle : (t('chatWelcome') || 'Welcome to ScholarGPT')}
            </h2>
          </div>

          
        </header>

        {/* Chat Area */}
        <ChatMessages
          messages={activeChat?.messages || []}
          isTyping={querying}
          messagesEndRef={messagesEndRef}
          loading={loading && !activeChat}
        />

        {/* Input Area */}
        <ChatInput />
      </div>

    </div>
  );
}
