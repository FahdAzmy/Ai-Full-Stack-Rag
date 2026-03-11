'use client';

import { useLanguage } from '@/lib/language-context';
import { useState, useRef, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '@/store/store';
import { sendQuery } from '@/store/chat/chat-actions';

export function ChatInput() {
  const { t } = useLanguage();
  const dispatch = useDispatch<AppDispatch>();
  const { activeChat, querying } = useSelector((state: RootState) => state.chat);
  const { selectedDocumentIds } = useSelector((state: RootState) => state.documents);

  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!value.trim() || querying || !activeChat) return;

    dispatch(
      sendQuery({
        chatId: activeChat.id,
        question: value.trim(),
        documentIds: selectedDocumentIds.length > 0 ? selectedDocumentIds : undefined,
      })
    );

    setValue('');
    // Reset textarea height
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
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

  const isDisabled = querying || !activeChat;

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
              !activeChat
                ? (t('chatSelectOrCreate') || 'Select or create a chat to start...')
                : querying
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
