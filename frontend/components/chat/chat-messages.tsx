'use client';

import React, { RefObject, useState, useMemo, useCallback, memo } from 'react';
import DOMPurify from 'dompurify';
import type { MessageResponse, SourceChunk } from '@/lib/api/chats';
import { SourcesPanel } from './sources-panel';
import { useLanguage } from '@/lib/language-context';

// ── Shared utility ──────────────────────────────────────────────────────────

function formatTime(dateStr: string): string {
  try {
    return new Date(dateStr).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

// ── ChatMessages (top-level export) ─────────────────────────────────────────

interface ChatMessagesProps {
  messages: MessageResponse[];
  isTyping: boolean;
  messagesEndRef: RefObject<HTMLDivElement | null>;
  loading?: boolean;
}

export const ChatMessages = memo(function ChatMessages({
  messages,
  isTyping,
  messagesEndRef,
  loading,
}: ChatMessagesProps) {
  const { t } = useLanguage();

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto chat-scrollbar p-6" role="status" aria-label="Loading messages">
        <div className="max-w-4xl mx-auto space-y-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse flex gap-4" aria-hidden="true">
              <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-full shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-3/4" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-1/2" />
                <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-2/3" />
              </div>
            </div>
          ))}
          <span className="sr-only">Loading messages, please wait...</span>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-6">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <span className="material-symbols-outlined text-3xl text-primary" aria-hidden="true">chat</span>
          </div>
          <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">
            {t('chatEmptyTitle') || 'Start a Conversation'}
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
            {t('chatEmptySubtitle') || 'Ask a question about your research papers to get AI-powered insights with source citations.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex-1 overflow-y-auto chat-scrollbar p-6"
      role="log"
      aria-label="Chat messages"
      aria-live="polite"
    >
      <div className="max-w-4xl mx-auto space-y-8">
        {messages.map((message) =>
          message.role === 'assistant' ? (
            <AssistantMessage key={message.id} message={message} />
          ) : (
            <UserMessage key={message.id} message={message} />
          )
        )}

        {/* Typing indicator */}
        {isTyping && !messages.some(m => m.id === 'streaming') && (
          <div className="flex gap-4 animate-in fade-in-0 slide-in-from-bottom-4 duration-300" role="status" aria-label="AI is typing">
            <div className="size-10 rounded-lg bg-teal-100 dark:bg-teal-900/40 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-teal-600 dark:text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
              </svg>
            </div>
            <div className="max-w-[80%]">
              <div className="bg-gray-100 dark:bg-gray-800 p-4 rounded-2xl rounded-tl-none shadow-sm">
                <div className="flex items-center gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-teal-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
            <span className="sr-only">AI is generating a response...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
});

// ── AssistantMessage ────────────────────────────────────────────────────────

const AssistantMessage = memo(function AssistantMessage({ message }: { message: MessageResponse }) {
  const { t } = useLanguage();
  const [showSources, setShowSources] = useState(false);
  const sources = useMemo(
    () => (message.source_chunks as SourceChunk[] | null) || [],
    [message.source_chunks],
  );
  const hasSources = sources.length > 0;

  // Sanitize HTML content to prevent XSS
  const sanitizedContent = useMemo(
    () => DOMPurify.sanitize(message.content),
    [message.content],
  );

  const toggleSources = useCallback(() => {
    setShowSources(prev => !prev);
  }, []);

  return (
    <div className="flex gap-4 animate-in fade-in-0 slide-in-from-bottom-4 duration-300" role="article" aria-label="AI response">
      {/* AI avatar */}
      <div className="size-8 rounded-full bg-primary dark:bg-emerald-600 flex items-center justify-center shrink-0 shadow-sm">
        <span className="material-symbols-outlined text-secondary dark:text-emerald-50 text-sm" aria-hidden="true">smart_toy</span>
      </div>
      <div className="flex flex-col gap-2 max-w-[85%]">
        <div
          className="bg-secondary dark:bg-gray-800 border border-border-cream dark:border-gray-700 text-primary dark:text-emerald-50 px-5 py-4 rounded-2xl rounded-tl-none shadow-sm space-y-4 text-sm leading-relaxed"
          dangerouslySetInnerHTML={{ __html: sanitizedContent }}
        />
        <div className="flex items-center gap-4">
          <time className="text-[10px] text-slate-400 font-medium" dateTime={message.created_at}>
            {formatTime(message.created_at)}
          </time>
          {/* View Sources button */}
          {hasSources && (
            <button
              onClick={toggleSources}
              aria-expanded={showSources}
              aria-label={`${showSources ? 'Hide' : 'View'} ${sources.length} sources`}
              className={`
                flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold transition-all
                ${showSources
                  ? 'bg-primary/10 text-primary dark:bg-primary/20 dark:text-primary-light'
                  : 'text-slate-400 hover:text-primary hover:bg-primary/5 dark:hover:text-primary-light'
                }
              `}
            >
              <span className="material-symbols-outlined text-sm" aria-hidden="true">menu_book</span>
              {t('viewSources') || 'View Sources'} ({sources.length})
            </button>
          )}
        </div>

        {/* Sources panel */}
        {showSources && hasSources && (
          <SourcesPanel sources={sources} />
        )}
      </div>
    </div>
  );
});

// ── UserMessage ─────────────────────────────────────────────────────────────

const UserMessage = memo(function UserMessage({ message }: { message: MessageResponse }) {
  return (
    <div className="flex gap-4 justify-end animate-in fade-in-0 slide-in-from-bottom-4 duration-300" role="article" aria-label="Your message">
      <div className="flex flex-col items-end gap-2 max-w-[80%]">
        <div className="bg-primary dark:bg-emerald-600 text-secondary dark:text-emerald-50 px-4 py-3 rounded-2xl rounded-tr-none shadow-sm text-start">
          <p className="text-sm leading-relaxed">{message.content}</p>
        </div>
        <time className="text-[10px] text-slate-400 font-medium block" dateTime={message.created_at}>
          {formatTime(message.created_at)}
        </time>
      </div>
      <div className="size-8 rounded-full bg-primary/20 dark:bg-emerald-500/20 flex items-center justify-center shrink-0">
        <span className="material-symbols-outlined text-primary dark:text-emerald-400 text-sm" aria-hidden="true">person</span>
      </div>
    </div>
  );
});
