'use client';

import { useRef, useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { ChatMessages } from './chat-messages';
import { ChatInput } from './chat-input';
import { DocumentSidebar } from '@/components/documents/document-sidebar';
import { useLanguage } from '@/lib/language-context';

export function ChatLayout() {
  const { t } = useLanguage();
  const { activeChat, querying, loading } = useSelector((state: RootState) => state.chat);
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
            <span className="material-symbols-outlined text-primary/40 dark:text-emerald-500/40">menu_open</span>
            <h2 className="text-sm font-semibold text-primary dark:text-emerald-400 truncate">
              {activeChat ? chatTitle : (t('chatWelcome') || 'Welcome to ScholarGPT')}
            </h2>
          </div>

          {/* Toggle document sidebar button */}
          <button
            onClick={() => setDocSidebarOpen(!docSidebarOpen)}
            className={`
              p-2 rounded-lg transition-colors hidden lg:flex items-center gap-2
              ${docSidebarOpen
                ? 'text-primary bg-primary/5 dark:bg-primary/10'
                : 'text-slate-400 hover:text-primary hover:bg-primary/5'
              }
            `}
            title={t('toggleDocPanel') || 'Toggle documents panel'}
          >
            <span className="material-symbols-outlined text-lg">description</span>
            <span className="text-xs font-semibold">{t('chatDocuments') || 'Documents'}</span>
          </button>
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

      {/* Right Document Sidebar */}
      <DocumentSidebar
        isOpen={docSidebarOpen}
        onToggle={() => setDocSidebarOpen(!docSidebarOpen)}
      />
    </div>
  );
}
