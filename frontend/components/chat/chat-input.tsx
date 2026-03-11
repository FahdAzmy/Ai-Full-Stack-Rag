'use client';

import { useLanguage } from '@/lib/language-context';
import { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
}

export function ChatInput({ onSend }: ChatInputProps) {
  const { t } = useLanguage();
  const [value, setValue] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!value.trim()) return;
    onSend(value.trim());
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

  return (
    <div className="p-6 bg-white dark:bg-background-dark border-t border-border-cream dark:border-gray-800 transition-colors">
      <div className="max-w-4xl mx-auto relative group">
        
        <div className="relative bg-background-light dark:bg-gray-900 border border-border-cream dark:border-gray-700 rounded-2xl p-2 shadow-sm focus-within:ring-2 focus-within:ring-primary/20 dark:focus-within:ring-emerald-500/20 focus-within:border-primary/40 dark:focus-within:border-emerald-500/50 transition-all">
          <textarea
            ref={inputRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-sm text-primary dark:text-emerald-100 placeholder-primary/40 dark:placeholder-emerald-500/40 min-h-[100px] resize-none px-4 pt-4"
            placeholder={t('chatPlaceholder') || "Ask ScholarGPT about research papers, methodologies, or data..."}
          />
          <div className="flex justify-end px-3 pb-2 pt-2 border-t border-border-cream/50 dark:border-gray-800 mt-2 transition-colors">
         
            <button
              onClick={handleSubmit}
              disabled={!value.trim()}
              className="bg-primary dark:bg-emerald-600 text-secondary dark:text-white px-5 py-2 rounded-xl text-sm font-bold flex items-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span>Analyze</span>
              <span className="material-symbols-outlined text-sm rtl:rotate-180">send</span>
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
