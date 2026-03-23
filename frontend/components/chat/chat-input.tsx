'use client';

import { useLanguage } from '@/lib/language-context';
import { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { 
  appendUserMessage, 
  startStreamingMessage, 
  appendTokenToStreamingMessage, 
  finalizeStreamingMessage, 
  setQuerying, 
  setChatError 
} from '@/store/chat/chat-slice';
import { getAccessToken } from '@/lib/axios';
import { createChat } from '@/store/chat/chat-actions';

export function ChatInput() {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { activeChat, querying } = useSelector((state: RootState) => state.chat);
  const { selectedDocumentIds } = useSelector((state: RootState) => state.documents);

  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = async () => {
    if (!value.trim() || querying) return;

    const questionToAsk = value.trim();
    setValue('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    dispatch(setQuerying(true));

    let chatId = activeChat?.id;

    if (!chatId) {
      // Create chat first! This thunk automatically sets the new chat as activeChat in Redux
      try {
        const actionResult = await dispatch(createChat(undefined)).unwrap();
        chatId = actionResult.id;
      } catch (err: any) {
        dispatch(setChatError(err.message || 'Failed to create chat'));
        dispatch(setQuerying(false));
        return;
      }
    }

    // Optimistic user message matches the now-active chat
    dispatch(appendUserMessage({
      id: `temp-${Date.now()}`,
      role: 'user',
      content: questionToAsk,
      source_chunks: null,
      created_at: new Date().toISOString(),
    }));

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const token = getAccessToken();
      
      const response = await fetch(`${apiUrl}/chats/${chatId}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          question: questionToAsk,
          document_ids: selectedDocumentIds.length > 0 ? selectedDocumentIds : null
        })
      });

      if (!response.ok) {
        throw new Error('Query failed');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let streamStarted = false;
      let buffer = '';

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // The last element in lines could be an incomplete chunk, so we keep it in the buffer
          buffer = lines.pop() || ''; 

          for (const line of lines) {
            if (line.trim() === '') continue;
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              if (!dataStr) continue;
              
              try {
                const data = JSON.parse(dataStr);
                
                if (data.type === 'sources') {
                  dispatch(startStreamingMessage({ sources: data.sources }));
                  streamStarted = true;
                } else if (data.type === 'chunk') {
                  if (!streamStarted) {
                    dispatch(startStreamingMessage({ sources: null }));
                    streamStarted = true;
                  }
                  dispatch(appendTokenToStreamingMessage(data.content));
                } else if (data.type === 'done') {
                  dispatch(finalizeStreamingMessage({ 
                    id: data.message_id, 
                    sources: data.sources,
                    title: data.chat_title
                  }));
                } else if (data.type === 'error') {
                  throw new Error(data.error);
                }
              } catch (e) {
                console.error('Error parsing SSE line:', line, e);
              }
            }
          }
        }
      }
    } catch (err: any) {
      dispatch(setChatError(err.message || 'An error occurred'));
      dispatch(setQuerying(false));
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 120) + 'px';
    }
  }, [value]);

  const isDisabled = querying;

  return (
    <div className="p-6 bg-white dark:bg-background-dark border-t border-border-cream dark:border-gray-800 transition-colors">
      <div className="max-w-4xl mx-auto relative group">
        {/* Document filter indicator */}
        {selectedDocumentIds.length > 0 && (
          <div className="mb-2 flex items-center gap-2 text-xs text-primary font-medium">
            <span className="material-symbols-outlined text-sm">filter_alt</span>
            {t('chatFilterActive') || `Filtering by ${selectedDocumentIds.length} document(s)`}
          </div>
        )}

        <div className={`
          relative bg-background-light dark:bg-gray-900 border border-border-cream dark:border-gray-700 rounded-2xl p-2 shadow-sm 
          focus-within:ring-2 focus-within:ring-primary/20 dark:focus-within:ring-emerald-500/20 
          focus-within:border-primary/40 dark:focus-within:border-emerald-500/50 transition-all
          ${isDisabled ? 'opacity-60' : ''}
        `}>
          <textarea
            ref={inputRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm text-primary dark:text-emerald-100 placeholder-primary/40 dark:placeholder-emerald-500/40 min-h-[100px] resize-none px-4 pt-4 disabled:cursor-not-allowed"
            placeholder={
              querying
                ? (t('chatGenerating') || 'Generating response...')
                : (t('chatPlaceholder') || 'Ask ScholarGPT about research papers, methodologies, or data...')
            }
          />
          <div className="flex justify-end px-3 pb-2 pt-2 border-t border-border-cream/50 dark:border-gray-800 mt-2 transition-colors">
            <button
              onClick={handleSubmit}
              disabled={!value.trim() || isDisabled}
              className="bg-primary dark:bg-emerald-600 text-secondary dark:text-white px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {querying ? (
                <>
                  <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                  <span>{t('chatAnalyzing') || 'Analyzing...'}</span>
                </>
              ) : (
                <>
                  <span>{t('chatAnalyze') || 'Analyze'}</span>
                  <span className="material-symbols-outlined text-sm rtl:rotate-180">send</span>
                </>
              )}
            </button>
          </div>
        </div>
        <p className="text-[10px] text-center text-slate-400 mt-3">
          {t('chatDisclaimer')}
        </p>
      </div>
    </div>
  );
}
