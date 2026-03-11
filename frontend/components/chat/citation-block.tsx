'use client';

import { useState } from 'react';
import type { SourceChunk } from '@/lib/api/chats';
import { formatAPA, formatMLA, formatBibTeX, copyToClipboard, CitationFormat } from '@/lib/api/citations';
import { useLanguage } from '@/lib/language-context';

interface CitationBlockProps {
  source: SourceChunk;
}

export function CitationBlock({ source }: CitationBlockProps) {
  const { t } = useLanguage();
  const [activeFormat, setActiveFormat] = useState<CitationFormat>('apa');
  const [copied, setCopied] = useState(false);

  const citations: Record<CitationFormat, string> = {
    apa: formatAPA(source),
    mla: formatMLA(source),
    bibtex: formatBibTeX(source),
  };

  const handleCopy = async () => {
    const success = await copyToClipboard(citations[activeFormat]);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const tabs: { key: CitationFormat; label: string }[] = [
    { key: 'apa', label: 'APA' },
    { key: 'mla', label: 'MLA' },
    { key: 'bibtex', label: 'BibTeX' },
  ];

  return (
    <div className="mt-2 rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-center justify-between bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
        <div className="flex">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveFormat(tab.key)}
              className={`
                px-3 py-1.5 text-xs font-bold transition-colors
                ${activeFormat === tab.key
                  ? 'text-primary border-b-2 border-primary bg-white dark:bg-slate-800'
                  : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-300'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <button
          onClick={handleCopy}
          className="px-2 py-1 mr-1 text-xs font-medium text-slate-500 hover:text-primary dark:text-slate-400 dark:hover:text-primary-light transition-colors flex items-center gap-1"
          title={t('copyCitation') || 'Copy citation'}
        >
          <span className="material-symbols-outlined text-sm">
            {copied ? 'check' : 'content_copy'}
          </span>
          {copied ? (t('copied') || 'Copied!') : (t('copy') || 'Copy')}
        </button>
      </div>

      {/* Citation content */}
      <div className={`
        p-3 text-xs leading-relaxed
        ${activeFormat === 'bibtex'
          ? 'font-mono bg-slate-900 text-emerald-300 dark:bg-slate-950 whitespace-pre'
          : 'text-slate-700 dark:text-slate-300 bg-white dark:bg-slate-800'
        }
      `}>
        {citations[activeFormat]}
      </div>
    </div>
  );
}
