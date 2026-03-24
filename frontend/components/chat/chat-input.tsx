'use client';

import React, { memo, useState, useRef, useEffect, useCallback } from 'react';
import { useLanguage } from '@/lib/language-context';
import { useSelector } from 'react-redux';
import { RootState } from '@/store/store';
import { useStreamingQuery } from '@/Hooks/use-streaming-query';

export const ChatInput = memo(function ChatInput() {
  const { t } = useLanguage();
  const { selectedDocumentIds, documents } = useSelector((state: RootState) => state.documents);
  const { sendQuery, abort, querying } = useStreamingQuery();

  const [value, setValue] = useState('');
  const [showDocError, setShowDocError] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Abort stream on unmount
  useEffect(() => {
    return () => abort();
  }, [abort]);

  const handleSubmit = useCallback(() => {
    if (!value.trim() || querying) return;

    if (!documents || documents.length === 0) {
      setShowDocError(true);
      setTimeout(() => setShowDocError(false), 3000);
      return;
    }

    const question = value.trim();
    setValue('');
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
    }

    sendQuery(question);
  }, [value, querying, documents, sendQuery]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }, [handleSubmit]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
  }, []);

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
          <div className="mb-2 flex items-center gap-2 text-xs text-primary font-medium" role="status">
            <span className="material-symbols-outlined text-sm" aria-hidden="true">filter_alt</span>
            {t('chatFilterActive') || 'Filtering by'} {selectedDocumentIds.length} {t('docDocuments') || 'document(s)'}
          </div>
        )}

        {/* Missing documents error popup */}
        {showDocError && (
          <div className="absolute -top-12 left-1/2 -translate-x-1/2 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/50 px-4 py-2 rounded-lg text-sm font-bold shadow-md animate-in fade-in slide-in-from-bottom-2 z-10 whitespace-nowrap flex items-center gap-2">
            <span className="material-symbols-outlined text-sm" aria-hidden="true">error</span>
            {t('uploadDocumentsFirst') || "You have to upload documents first to start chatting."}
          </div>
        )}

        <form
          onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
          className={`
            relative bg-background-light dark:bg-gray-900 border border-border-cream dark:border-gray-700 rounded-2xl p-2 shadow-sm 
            focus-within:ring-2 focus-within:ring-primary/20 dark:focus-within:ring-emerald-500/20 
            focus-within:border-primary/40 dark:focus-within:border-emerald-500/50 transition-all
            ${isDisabled ? 'opacity-60' : ''}
          `}
          role="search"
          aria-label="Ask a research question"
        >
          <label htmlFor="chat-input" className="sr-only">
            {t('chatPlaceholder') || 'Ask AskAnyDoc about documents, methodologies, or data...'}
          </label>
          <textarea
            id="chat-input"
            ref={inputRef}
            value={value}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={isDisabled}
            aria-describedby="chat-disclaimer"
            className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm text-primary dark:text-emerald-100 placeholder-primary/40 dark:placeholder-emerald-500/40 min-h-[100px] resize-none px-4 pt-4 disabled:cursor-not-allowed"
            placeholder={
              querying
                ? (t('chatGenerating') || 'Generating response...')
                : (t('chatPlaceholder') || 'Ask AskAnyDoc about documents, methodologies, or data...')
            }
          />
          <div className="flex justify-end px-3 pb-2 pt-2 border-t border-border-cream/50 dark:border-gray-800 mt-2 transition-colors">
            <button
              type="submit"
              disabled={!value.trim() || isDisabled}
              aria-label={querying ? 'Analyzing your question...' : 'Send your question'}
              className="bg-primary dark:bg-emerald-600 text-secondary dark:text-white px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {querying ? (
                <>
                  <span className="material-symbols-outlined text-sm animate-spin" aria-hidden="true">progress_activity</span>
                  <span>{t('chatAnalyzing') || 'Analyzing...'}</span>
                </>
              ) : (
                <>
                  <span>{t('chatAnalyze') || 'Analyze'}</span>
                  <span className="material-symbols-outlined text-sm rtl:rotate-180" aria-hidden="true">send</span>
                </>
              )}
            </button>
          </div>
        </form>
        <p id="chat-disclaimer" className="text-[10px] text-center text-slate-400 mt-3">
          {t('chatDisclaimer')}
        </p>
      </div>
    </div>
  );
});
